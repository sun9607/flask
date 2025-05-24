import datetime
import json
import os
import jwt
import requests
from apscheduler.schedulers.background import BackgroundScheduler

import logging
from logging.handlers import RotatingFileHandler

import traceback

from apscheduler.triggers.cron import CronTrigger
from flask import redirect, request, jsonify, send_from_directory, abort, make_response, session, url_for, Response
from flask_cors import CORS, cross_origin
from pytz import timezone

from auth.naver import get_token
from service.file_control import delete_file
from service.order import check_order
from service.production import save_form, show_invitation, save_premium, get_premium, save_user, get_user, set_user, \
    retrieve_my_cards, remove_cards, edit_card, remove_temp, set_order_card, delete_a_card
from util.appsettings import app, UPLOAD_FOLDER

CORS(app, supports_credentials=True, origins="http://localhost:3000")

# 로그 파일 핸들러 설정
handler = RotatingFileHandler('flask_error.log', maxBytes=10000, backupCount=5, encoding='utf-8')
handler.setLevel(logging.ERROR)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s in %(pathname)s:%(lineno)d'
)
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.ERROR)


@app.route("/health")
def health_check():
    return "ok"


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"})
    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"})

    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    filename = file.filename
    base, ext = os.path.splitext(filename)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename_with_time = f"{base}_{timestamp}{ext}"
    filepath = os.path.join("uploads", filename_with_time)
    file.save(filepath)

    file_url = url_for("uploaded_file", filename=filename_with_time)

    return jsonify({"file_url": file_url})


@app.route("/delete_file", methods=["DELETE"])
def file_delete():
    file_path = request.form.get("path")
    return delete_file(file_path)


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except Exception as e:
        return Response(f"Error: {str(e)}", status=500, mimetype="text/plain")


@app.route("/save", methods=["POST"])
def save_data():
    data = request.form
    remove_temp(data['id'])
    data_id = save_form(data, is_temp=False)
    if data_id:
        return jsonify({"id": data_id})
    else:
        return abort(500)


@app.route("/temp", methods=["POST"])
def save_temp():
    data = request.form
    remove_temp(data['id'])
    data_id = save_form(data, is_temp=True)
    if data_id:
        return jsonify({"id": data_id})
    else:
        return abort(500)


@app.route("/premium-abcd", methods=["POST"])
def add_premium():
    card_id = request.form["id"]
    result = save_premium(card_id)
    if result:
        return "ok"
    else:
        return abort(500)


@app.route("/card")
def produce_invitation():
    card_id = request.args.get("id")
    result = show_invitation(card_id)
    if result is None:
        abort(500)
    else:
        return jsonify(result)


@app.route("/card", methods=["PUT"])
def update_card():
    data = request.form
    result = edit_card(data)
    if result:
        return "ok"
    else:
        return abort(500)


@app.route("/card_user", methods=["PUT"])
def update_card_user():
    user_id = request.form.get("userId")
    card_id = request.form.get("cardId")
    result = set_user(user_id, card_id)
    if result:
        return "ok"
    else:
        return abort(500)


@app.route("/get-my-cards")
def get_my_cards():
    user_id = request.args.get("user_id")
    cards = retrieve_my_cards(user_id)
    return cards


@app.route("/login/naver")
def naver_login():
    code = request.args.get("code")
    state = request.args.get("state")
    naver_client_id = os.environ.get('NAVER_CLIENT_ID')
    naver_secret = os.environ.get('NAVER_CLIENT_SECRET')
    token_url = f"https://nid.naver.com/oauth2.0/token?grant_type=authorization_code&response_type=code&client_id={naver_client_id}&client_secret={naver_secret}&redirect_uri=https://heliumgas.kr&code={code}&state={state}"
    response = requests.get(token_url)
    if response.status_code == 200:
        access_token = response.json()['access_token']
        user_url = "https://openapi.naver.com/v1/nid/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_response = requests.get(user_url, headers=headers)
        if user_response.status_code == 200:
            user_info = user_response.json().get("response")
            user_id = user_info.get("id")
            user_email = user_info.get("email")
            user_name = user_info.get("name")
            token = jwt.encode(
                {'username': user_name, 'userid': user_id, 'email': user_email,
                 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)},
                os.environ.get('JWT_SECRET'))

            if not get_user(id=user_id, name=user_name):
                # 회원가입 되지 않은 회원 DB저장
                save_user(id=user_id, name=user_name)

            response = make_response(redirect('https://heliumgas.kr'))
            response.set_cookie('ssid', token, httponly=True, max_age=30 * 24 * 60 * 60, domain="heliumgas.kr",
                                samesite="None", secure=True)

            return response
        else:
            return "Failed to fetch user info", 400
    else:
        return "Failed to fetch access token", 400


@app.route("/delete-card", methods=["DELETE"])
def delete_card():
    card_id = request.args.get("cardId")
    return delete_a_card(card_id)


@app.route("/remove-watermark", methods=["PUT"])
def remove_watermark():
    try:
        if not request.data:
            app.logger.warning("빈 요청: body 없음 - %s", request.path)
            return jsonify({"error": "빈 요청 본문입니다."}), 400

        try:
            data_json = json.loads(request.data.decode("utf-8"))
        except Exception as e:
            app.logger.warning("JSON 파싱 실패: %s - body=%s", str(e), repr(request.data))
            return jsonify({"error": "잘못된 JSON 형식입니다."}), 400

        order_id = data_json.get("orderId")
        card_id = data_json.get("cardId")

        if not order_id or not card_id:
            app.logger.warning("필수 필드 누락: orderId=%s, cardId=%s", order_id, card_id)
            return jsonify({"error": "'orderId'와 'cardId'는 필수입니다."}), 400

        try:
            token = get_token()
        except Exception as e:
            app.logger.error("토큰 발급 실패: %s\n%s", str(e), traceback.format_exc())
            return jsonify({"error": "인증 토큰 발급 실패"}), 500

        status, result, data = check_order(token, order_id)

        if status != 200:
            app.logger.error("check_order 실패: status=%s, orderId=%s", status, order_id)
            return jsonify({"error": f"주문 조회 실패 (status={status})"}), status

        if not result:
            app.logger.info("주문 내역 없음: orderId=%s", order_id)
            return jsonify({
                "result": False,
                "message": "주문 내역이 없습니다."
            })

        try:
            res, message = set_order_card(order_id, card_id)
        except Exception as e:
            app.logger.error("set_order_card 실패: %s\n%s", str(e), traceback.format_exc())
            return jsonify({"error": "카드 설정 실패"}), 500

        return jsonify({
            "result": res,
            "message": message
        })

    except Exception as e:
        app.logger.error("remove_watermark() 예외 발생: %s\n%s", str(e), traceback.format_exc())
        return jsonify({"error": "서버 내부 오류가 발생했습니다."}), 500


seoul_timezone = timezone("Asia/Seoul")
scheduler = BackgroundScheduler(timezone=seoul_timezone)
scheduler.add_job(remove_cards, CronTrigger(hour=0, minute=0, second=0, timezone=seoul_timezone))
scheduler.start()

@app.errorhandler(Exception)
def handle_exception(e):
    tb = traceback.format_exc()
    app.logger.error("Unhandled Exception:\n%s", tb)
    return jsonify({"error": "Internal Server Error"}), 500

if __name__ == "__main__":
    app.run(debug=True)
