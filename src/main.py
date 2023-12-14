import os
import mysql.connector
from twilio.rest import Client
import uuid
from datetime import datetime
from backports.zoneinfo import ZoneInfo
from dotenv import load_dotenv
import sentry_sdk

class TwilioDataProcessor:
    
    def __init__(self):
        load_dotenv()

        # Environment variables
        self.config = {
            'host': os.environ['DB_HOST'],
            'user': os.environ['DB_USER'],
            'password': os.environ['DB_PASSWORD'],
            'database': os.environ['DB_DATABASE'],
        }
        
        self.status_info = {
        "queued": {"status":4, "message": "只今店舗への連絡を行っております","title":"お問い合わせ中"},
        "initiated": {"status":4, "message": "只今店舗への連絡を行っております","title":"お問い合わせ中"},
        "in-progress": {"status":4, "message": "只今店舗への連絡を行っております","title":"お問い合わせ中"},
        "ringing": {"status":4, "message": "只今店舗への連絡を行っております","title":"お問い合わせ中"},
        "completed": {"status":4, "message": "只今店舗への連絡を行っております","title":"お問い合わせ中"},
        "busy": {"status":2, "message": "店舗が電話をとりませんでした。しばらく時間をおいて再度を予約をしてください","title":"お問い合わせ失敗"},
        "failed": {"status":8, "message": "電話の発信ができませんでした。しばらく時間をおいて再度を予約をしてください","title":"エラー発生"},
        "no-answer": {"status":6, "message": "店舗が電話をとりませんでした。しばらく時間をおいて再度を予約をしてください","title":"お問い合わせ失敗"},
    }


    def get_call_details(self,call_sid):
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

    def convert_id_to_sid(self,id_value):
        """
        指定されたIDに対応するSIDをデータベースから検索して出力する関数

        """
        # データベースへの接続とカーソルの作成
        connection = mysql.connector.connect(**self.config)
        cursor = connection.cursor()
    
        query = f"SELECT sid FROM main_app_reservationparent WHERE id='{id_value}' and sid!=''"
        # query = f"SELECT sid FROM main_app_reservationparent"
        cursor.execute(query)

        results = cursor.fetchall()
        for (sid,) in results:
            return sid

    def insert_data_to_child(self,config, data):
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

    def change_parent_status(self,config, parent_id):
        """
        main_app_reservationparentのstatusを0から1へ変更する
        """
    
        try:
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()

        
            # update_query = (
            #     "UPDATE main_app_reservationparent "
            #     "SET is_end=1 "
            #     "WHERE id='%s'"
            # )
            
            update_query = f"UPDATE main_app_reservationparent SET is_end=1 WHERE id='{parent_id}'"

        
            # cursor.execute(update_query, (parent_id,))
            cursor.execute(update_query)

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

    def get_non_end_ids(self,config):
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
            
    # def get_parent_ids_compleated_from_child(self,config):
    #     """
    #     statusが1のmain_app_reservationchildのparent_idをリストで取得
    #     """
    #     # MySQLデータベースに接続
    #     conn = mysql.connector.connect(**config)
    #     cursor = conn.cursor()

    #     try:
    #         # main_app_reservationchildのstatusが1の項目のparent_idを取得するクエリ
    #         query = "SELECT parent_id FROM main_app_reservationchild WHERE status = 1"
    #         cursor.execute(query)

    #         result = cursor.fetchall()

    #         return [row[0] for row in result]

    #     except mysql.connector.Error as err:
    #         print(f"Error: {err}")
    #         return []

    #     finally:
    #         cursor.close()
    #         conn.close()
    
    def main(self):
        
        sentry_sdk.init(
        dsn=os.environ['SENTRY_URL'],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
        )


        for id_value in self.get_non_end_ids(self.config):
            sid = self.convert_id_to_sid(id_value)
            if sid:
                try:
                    status = self.get_call_details(sid)

                    unique_id = str(uuid.uuid4()).replace('-', '')

                    data = {
                        'id': unique_id,
                        'datetime': str(datetime.now()),
                        'status': str((lambda key: self.status_info.get(key, {}).get('status', 'none'))(status["Status"])),
                        'title': (lambda key: self.status_info.get(key, {}).get('title', 'none'))(status["Status"]),
                        'message': (lambda key: self.status_info.get(key, {}).get('message', 'none'))(status["Status"]),
                        'parent_id': id_value
                    }
                    
                    self.insert_data_to_child(self.config,data)
                    
                    if data["status"]=="2" or data["status"]=="6":
                        self.change_parent_status(self.config,id_value)
                except Exception as e:
                    print(e)
                    continue
            
                

        

if __name__ == "__main__":
    twilio_processor = TwilioDataProcessor()
    twilio_processor.main()