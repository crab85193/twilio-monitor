import os
import mysql.connector
from twilio.rest import Client
import uuid
import datetime
from datetime import datetime
from backports.zoneinfo import ZoneInfo
import mysql.connector
from dotenv import load_dotenv
time = datetime.now(ZoneInfo('Asia/Tokyo'))

load_dotenv(".env")

#環境変数から設定を取得
config = {
    'host': os.environ['DB_HOST'],
    'user': os.environ['DB_USER'],
    'password': os.environ['DB_PASSWORD'],
    'database': os.environ['DB_DATABASE'],
    }






def get_call_details(call_sid):
    """
    twilioサービスから通話情報の詳細を取得する関数
    call_detailsにある項目は取得可能

    """
    account_sid = os.environ['account_sid']
    auth_token = os.environ['auth_token']

    client = Client(account_sid, auth_token)
    call = client.calls(call_sid).fetch()
    
    call_details = {
        # "Call SID": call.sid,
        # "From": call.from_formatted,
        # "To": call.to_formatted,
        "Status": call.status,
        # "Start Time": str(call.start_time),
        # "End Time": str(call.end_time),
        # "Duration": call.duration,
        # "Price": call.price,
        # "Price Unit": call.price_unit
    }

    return call_details

status_info = {
    "queued": {"status":1, "message": "通話がキューに入れられている状態"},
    "initiated": {"status":2, "message": "通話が開始されている状態"},
    "in-progress": {"status":3, "message": "通話が進行中である状態"},
    "ringing": {"status":4, "message": "通話が鳴っている状態"},
    "completed": {"status":5, "message": "通話が完了した状態"},
    "busy": {"status":6, "message": "通話が相手先で応答されずに忙しい状態"},
    "failed": {"status":7, "message": "通話が失敗した状態"},
    "no-answer": {"status":8, "message": "通話が相手先で応答がなかった状態"},
}



def convert_id_to_sid(id_value):
    """
    指定されたIDに対応するSIDをデータベースから検索して出力する関数

    """
    # データベースへの接続とカーソルの作成
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()
    
   
    query = "SELECT SID FROM main_app_reservationparent WHERE ID = %s"
    cursor.execute(query, (id_value,))

    results = cursor.fetchall()
    for (sid,) in results:
        return sid


def insert_data_to_child(config, data):
    """
    指定されたデータをデータベースの main_app_reservationchild テーブルに挿入する関数
    twilioからのデータ及びstatus番号を作成する
    """
    
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

     
        insert_query = (
            "INSERT INTO main_app_reservationchild (id, datetime, status, title, message, parent_id) "
            "VALUES (%s, %s, %s, %s, %s, %s)"
        )

        
        cursor.execute(insert_query, (
            data['id'], data['datetime'], data['status'], data['title'], 
            data['message'], data['parent_id']
        ))

    
        conn.commit()

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return False
    except Exception as err:
        print(f"An error occurred: {err}")
        return False
    finally:
    
        if conn.is_connected():
            cursor.close()
            conn.close()
    
    return True



def change_parent_status(config, parent_id):
    """
    main_app_reservationparentのstatusを0から1へ変更する
    """
   
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

    
        update_query = (
            "UPDATE main_app_reservationparent "
            "SET is_end = 1 "
            "WHERE id = %s"
        )

    
        cursor.execute(update_query, (parent_id,))

        conn.commit()

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return False
    except Exception as err:
        print(f"An error occurred: {err}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    return True

def get_non_end_ids(config):
    """
    is_endが0のidをリストで取得
    """
    
    # MySQLデータベースに接続
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    try:
        
        query = "SELECT id FROM main_app_reservationparent WHERE is_end != 1"
        cursor.execute(query)

      
        result = cursor.fetchall()

        # 取得したidのリストを返す
        return [row[0] for row in result]

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []

    finally:
       
        cursor.close()
        conn.close()
        
import mysql.connector

def get_parent_ids_compleated_from_child(config):
    """
    statusが1のmain_app_reservationchildのparent_idをリストで取得
    """
    # MySQLデータベースに接続
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    try:
        # main_app_reservationchildのstatusが1の項目のparent_idを取得するクエリ
        query = "SELECT parent_id FROM main_app_reservationchild WHERE status = 1"
        cursor.execute(query)

        result = cursor.fetchall()

        return [row[0] for row in result]

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []

    finally:
        cursor.close()
        conn.close()
   

def exac():
   
    for id_value in get_non_end_ids(config):
        
        status=get_call_details(convert_id_to_sid(id_value))
        
        id = uuid.uuid4() 
        id = str(id)
        id = id.replace('-', '')
        
        data = {
            'id':id,
            'datetime': str(datetime.now()),
            'status': str((lambda key: status_info.get(key, {}).get('status', 'Unknown'))(status["Status"])),
            'title':status["Status"],
            'message': (lambda key: status_info.get(key, {}).get('message', '情報がありません'))(status["Status"]),
            'parent_id': id_value
        }
        
        insert_data_to_child(config, data)
        
    
    for parent_ids in get_parent_ids_compleated_from_child(config):
        change_parent_status(config, parent_ids) #親のstatusを０から１へ変更
    
#example
exac()
