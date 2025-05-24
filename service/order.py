import http.client
import json
from urllib.parse import quote

def check_order(token, order_id):
    # URL 인코딩 (한글, 공백 등 대비)
    encoded_order_id = quote(order_id, safe="")
    
    conn = http.client.HTTPSConnection("api.commerce.naver.com")
    headers = {"Authorization": f"Bearer {token}"}

    try:
        conn.request("GET", f"/external/v1/pay-order/seller/orders/{encoded_order_id}/product-order-ids", headers=headers)
        res = conn.getresponse()

        if res.status == 200:
            data = res.read().decode("utf-8")
            to_json = json.loads(data)
            product_order_list = to_json.get("data", [])
            if not product_order_list:
                return 200, False, []
            return 200, True, product_order_list

        return res.status, False, []

    finally:
        conn.close()
