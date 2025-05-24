import os.path
import json
import datetime as dt
import logging

from models.card import Card, Gallery, db
from util.config import insert_data, query_data
from service.file_control import delete_file_by_path


def to_form(key):
    return "%s"


def get_value(data, key):
    if key in data:
        return data[key]
    return "NULL"


def get_string_value(data, key):
    value = get_value(data, key)
    if value != "NULL":
        return f"'{value}'"
    return value


def remove_temp(data_id):
    remove_query = "DELETE FROM invitationcard_db.card " \
                   f"WHERE id='{data_id}'"
    insert_data(remove_query)

    gallery_remove_query = "DELETE FROM invitationcard_db.gallery " \
                           f"WHERE card_no='{data_id}'"
    insert_data(gallery_remove_query)


def save_form(data, is_temp=True):
    keys = ["id", "name", "you", "bgm", "cover", "intro_layout", "intro_head", "intro_image", "particle", "intro_foot", "intro_type",
            "font_family", "font_size", "color", "letter", "prevent", "scroll",
            "letter_use_yn", "letter_font_family", "letter_design", "menu", "gallery_type",
            "video_use_yn", "video_title", "video_link", "video_file", "userId", "paid", "registerdate",
            "gallery_use_yn", "gallery_title", "temp_yn"]

    card_query = "INSERT INTO card " \
                "(" + ", ".join(keys) + ") " \
                f"VALUES ({get_string_value(data, 'id')}, {get_string_value(data, 'name')}, " \
                f"{get_string_value(data, 'you')}, {get_value(data, 'bgm')}, {get_value(data, 'cover')}, " \
                f"{get_value(data, 'intro_layout')}, {get_string_value(data, 'intro_head')}, " \
                f"{get_string_value(data, 'intro_image')}, {get_value(data, 'particle')}, {get_string_value(data, 'intro_foot')}, {get_string_value(data, 'intro_type')}, " \
                f"'{data['font_family']}', '{data['font_size']}', " \
                f"{get_string_value(data, 'color')}, {get_string_value(data, 'letter')}, {get_value(data, 'prevent')}, {get_value(data, 'scroll')}, " \
                f"{get_value(data, 'letter_use_yn')}, {get_string_value(data, 'letter_font_family')}, " \
                f"{get_value(data, 'letter_design')}, {get_string_value(data, 'menu')}, {get_value(data, 'gallery_type')}, " \
                f"{get_value(data, 'video_use_yn')}, {get_string_value(data, 'video_title')}, {get_string_value(data, 'video_link')}, {get_string_value(data, 'video_file')}, " \
                f"{get_string_value(data, 'user_id')}, 0, CURDATE(), {get_value(data, 'gallery_use_yn')}, {get_string_value(data, 'gallery_title')}"
    if is_temp:
        card_query += ", 1)"
    else:
        card_query += ", 0)"

    card_success = insert_data(card_query)

    gallery_data = json.loads(data["gallery"])

    gallery_query = "INSERT INTO gallery (card_no, photo, text) VALUES (%s, %s, %s)"
    for item in gallery_data:
        url = item.get("url")
        text = item.get("name", "")
        if url:
            gallery_success = insert_data(gallery_query, (data["id"], url, text))
            if not gallery_success:
                return False

    if card_success:
        return True
    return False


def get_photo_url(obj):
    return obj['photo']


def select_card(card_id):
    card_query = "SELECT * FROM invitationcard_db.card " \
                 f"WHERE id='{card_id}'"
    card_result = query_data(card_query)[0]
    return card_result


def get_set_field(data, field_name):
    return f"{field_name} = {get_string_value(data, field_name)}"


def join_values(data):
    keys = ["name", "you", "bgm", "cover", "intro_layout", "intro_head", "intro_image", "particle", "intro_foot", "intro_type",
            "font_family", "font_size", "color", "letter", "prevent", "scroll",
            "letter_use_yn", "letter_font_family", "letter_design", "menu", "gallery_type",
            "video_use_yn", "video_title", "video_link", "video_file", "paid",
            "gallery_use_yn", "gallery_title"]
    mapped = map(lambda x: get_set_field(data, x), keys)
    return ", ".join(list(mapped))


def edit_card(data):
    card_query = "UPDATE invitationcard_db.card " \
        f"SET {join_values(data)} " \
        f"WHERE id = '{data['id']}'"
    card_success = insert_data(card_query)
    if not card_success:
        return False

    # 기존 갤러리 삭제
    gallery_delete_query = f"DELETE FROM invitationcard_db.gallery WHERE card_no='{data['id']}'"
    gallery_delete_success = insert_data(gallery_delete_query)
    if not gallery_delete_success:
        return False

    # 새 갤러리 입력
    try:
        if isinstance(data['gallery'], str):
            gallery_list = json.loads(data['gallery'])
        else:
            gallery_list = data['gallery']
    except Exception as e:
        print(f"[ERROR] gallery 파싱 오류: {e}")
        return False

    gallery_query = "INSERT INTO gallery (card_no, photo, text) VALUES (%s, %s, %s)"
    for item in gallery_list:
        url = item.get("url", "")
        text = item.get("name", "")
        if url:
            insert_data(gallery_query, (data['id'], url, text))

    return True


def show_invitation(card_id):
    card_result = select_card(card_id)
    if card_result is None:
        return None

    gallery_query = f"SELECT photo, text, type FROM gallery WHERE card_no='{card_id}'"
    gallery_result = query_data(gallery_query)

    return {
        "bgm": card_result['bgm'],
        "cover": card_result["cover"],
        "myName": card_result["name"],
        "yourName": card_result["you"],
        "intro": {
            "layout": card_result['intro_layout'],
            "head": card_result['intro_head'],
            "image": card_result['intro_image'],
            "particle": card_result['particle'],
            "foot": card_result['intro_foot'],
            "introType": card_result['intro_type'],
        }, "theme": {
            "fontFamily": card_result['font_family'],
            "fontSize": card_result['font_size']
        },
        "color": card_result['color'],
        "letter": {
            "use_yn": card_result['letter_use_yn'],
            "font_family": card_result['letter_font_family'],
            "design": card_result['letter_design'],
            "text": card_result['letter']
        },
        "last_show_yn": card_result['last_show_yn'],
        "gallery": {
            "title": card_result["gallery_title"],
            "useYn": card_result["gallery_use_yn"],
            "type": card_result['gallery_type'],
            "files": gallery_result
        },
        "video": {
            "use_yn": card_result["video_use_yn"],
            "title": card_result["video_title"],
            "link": card_result["video_link"],
            "file": card_result["video_file"]
        },
        "menu": card_result['menu'],
        "prevent": card_result['prevent'],
        "scroll": card_result["scroll"],
        "userId": card_result["userId"],
        "orderId": card_result["order_id"]
    }


def save_premium(card_id):
    card = select_card(card_id)
    if card is None:
        return None

    query = "INSERT INTO invitationcard_db.premium_card (card_id) " \
            f"VALUES ('{card_id}')"
    success = insert_data(query)
    if success:
        return True
    return False


def get_premium(premium_id):
    query = "SELECT card_id FROM invitationcard_db.premium_card " \
            f"WHERE idx={premium_id}"
    result = query_data(query)[0]["card_id"]
    return result


def set_user(user_id, card_id):
    query = "UPDATE invitationcard_db.card " \
            f"SET userId='{user_id}' " \
            f"WHERE id='{card_id}'"
    result = insert_data(query)
    return result


def retrieve_my_cards(user_id):
    query = "SELECT * FROM invitationcard_db.card " \
            f"WHERE userId='{user_id}' " \
            f"ORDER BY registerdate DESC"
    result = query_data(query)
    return result


def get_user(id, name):
    user = f"SELECT * FROM users WHERE name='{name}' AND naver_client_id='{id}'"
    user_result = query_data(user)
    return user_result


def save_user(id, name):
    query = f"INSERT INTO invitationcard_db.users (name, naver_client_id) VALUES ('{name}', '{id}')"
    success = insert_data(query)
    if success:
        return True
    return False


def delete_a_card(card_id):
    try:
        logging.info(f"[삭제 시작] card_id: {card_id}")

        card = Card.query.filter_by(id=card_id).first()
        if not card:
            logging.warning(f"[삭제 실패] 카드 없음: {card_id}")
            return "편지가 존재하지 않습니다.", 404

        # 카드 정보 로그
        logging.info(f"[카드 삭제] 카드 정보: {card}")

        db.session.delete(card)

        # 파일 삭제
        if card.intro_image:
            logging.info(f"[파일 삭제] intro_image: {card.intro_image}")
            delete_file_by_path(card.intro_image)

        if card.video_file:
            logging.info(f"[파일 삭제] video_file: {card.video_file}")
            delete_file_by_path(card.video_file)

        # 갤러리 처리
        gallery = Gallery.query.filter_by(card_no=card_id).all()
        logging.info(f"[갤러리 항목] {len(gallery)}개 삭제 예정")

        for row in gallery:
            if row.photo:
                logging.info(f"[갤러리 파일 삭제] {row.photo}")
                delete_file_by_path(row.photo)
            db.session.delete(row)

        db.session.commit()
        logging.info(f"[삭제 완료] 카드 ID: {card_id}")
        return "편지를 삭제했습니다.", 200

    except Exception as e:
        logging.exception(f"[삭제 오류] 카드 삭제 실패: {str(e)}")
        return "서버 내부 오류", 500


def remove_cards():
    try:
        logging.info("remove_cards 실행 시작")
        two_months_ago = dt.datetime.now() - dt.timedelta(days=30)

        # gallery 테이블에서 관련 데이터 삭제 전 파일 제거
        card_ids_to_remove = Card.query.filter(
            Card.registerdate <= two_months_ago,  # 2달 전 데이터 필터링
            Card.order_id.isnot(None)  # order_id가 NULL이 아닌 데이터만 필터링
        ).with_entities(Card.id).all()  # 삭제할 카드 ID만 조회

        # gallery table에서 데이터 삭제 전 파일 제거
        galleries_to_remove = Gallery.query.filter(
            Gallery.card_no.in_([card_id[0] for card_id in card_ids_to_remove]),  # 조회된 카드 ID로 필터링
            Gallery.photo.like('https://%')  # photo URL 조건 추가
        ).all()

        for gallery in galleries_to_remove:
            if gallery.photo:
                delete_file_by_path(gallery.photo)

        # gallery table data delete
        Gallery.query.filter(
            Gallery.card_no.in_([card_id[0] for card_id in card_ids_to_remove]),
            Gallery.photo.like("https://%")
        ).delete(synchronize_session=False)

        cards_to_remove = Card.query.filter(
            Card.registerdate <= two_months_ago,
            Card.order_id.isnot(None),
            Card.intro_image.like('https://%')
        ).all()

        for card in cards_to_remove:
            if card.intro_image:
                delete_file_by_path(card.intro_image)

        Card.query.filter(
            Card.registerdate <= two_months_ago,
            Card.order_id.isnot(None),
            Card.intro_image.like('https://%')
        ).delete(synchronize_session=False)

        db.session.commit()
        print("데이터 삭제 및 커밋 성공")
        logging.info("remove_cards 실행 완료")
    
    except Exception as e:
        db.session.rollback()
        print(f"에러 발생: {e}")
        logging.error(f"remove_cards 실행 실패: {e}")


def set_order_card(order_id, card_id):
    ordered = Card.query.filter_by(order_id=order_id).first()
    if ordered:
        return False, "이미 사용한 주문입니다."
    card = Card.query.filter_by(id=card_id).first()
    if not card:
        return False, "없는 편지 입니다."
    card.order_id = order_id
    card.registerdate = dt.datetime.now()
    db.session.commit()
    return True, "워터마크가 제거 되었습니다. 구매한 카드는 한달 뒤 자동 삭제됩니다."
