import io
import mimetypes
import os

from flask import jsonify, url_for, send_file


def delete_file_by_path(pathname):
    if len(pathname):
        filename = pathname.split("/uploads/")[1]
        path = f"uploads/{filename}"
        if os.path.exists(path):
            os.remove(path)


def delete_file(path):
    if not path:
        return jsonify({"error": "파일 경로를 제공해야 합니다."}), 400
    if os.path.exists(path):
        os.remove(path)
        return jsonify({"message": "파일이 성공적으로 삭제되었습니다."})
    else:
        return jsonify({"error": "해당 파일을 찾을 수 없습니다."}), 404


def get_mime_type(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type


def read_uploaded_file(filename):
    upload_directory = os.path.abspath("uploads")
    path = os.path.join(upload_directory, filename)

    if os.path.exists(path):
        with open(path, "rb") as file:
            image_data = file.read()
        mimetype = get_mime_type(path)

        return send_file(
            io.BytesIO(image_data),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    else:
        response_data = {"status": "error", "message": "Image file not found"}
        return jsonify(response_data), 404