import os
import uuid
from datetime import datetime
import MySQLdb
from twilio.rest import Client

class TwilioMonitor:
    NOSTATE = 0
    START   = 1
    FAILURE = 2
    SUCCESS = 3
    WAIT    = 4
    CANCEL  = 5
    END     = 6
    SYSTEM  = 7
    ERROR   = 8
    UNKNOWN = 9
    
    STATUS_INFO = {
        "queued"     : {"status": WAIT   , "message": "只今店舗への連絡を行っております"                                    , "title":"お問い合わせ中"             },
        "initiated"  : {"status": WAIT   , "message": "只今店舗への連絡を行っております"                                    , "title":"お問い合わせ中"             },
        "in-progress": {"status": WAIT   , "message": "只今店舗への連絡を行っております"                                    , "title":"お問い合わせ中"             },
        "ringing"    : {"status": WAIT   , "message": "只今店舗への連絡を行っております"                                    , "title":"お問い合わせ中"             },
        "completed"  : {"status": WAIT   , "message": "只今店舗への連絡を行っております"                                    , "title":"お問い合わせ中"             },
        "busy"       : {"status" :FAILURE, "message": "店舗が電話をとりませんでした。しばらく時間をおいて再度を予約をしてください。", "title":"店舗様が通話中です"          },
        "failed"     : {"status": ERROR  , "message": "電話の発信ができませんでした。しばらく時間をおいて再度を予約をしてください。", "title":"電話の発信ができませんでした"  },
        "no-answer"  : {"status": FAILURE, "message": "店舗が電話をとりませんでした。しばらく時間をおいて再度を予約をしてください。", "title":"店舗様が電話をとりませんでした"},
    }

    CHILDSTATUS = (
        (NOSTATE, 'NoState'),
        (START,   'Start'  ),
        (FAILURE, 'Failure'),
        (SUCCESS, 'Success'),
        (WAIT   , 'Wait'   ),
        (CANCEL , 'Cancel' ),
        (END    , 'End'    ),
        (SYSTEM , 'System' ),
        (ERROR  , 'Error'  ),
        (UNKNOWN, 'Unknown'),
    )

    def __init__(self):
        self.__db = MySQLdb.connect(
            host=os.environ.get("MYSQL_HOST"),
            user=os.environ.get("MYSQL_USER"),
            passwd=os.environ.get("MYSQL_PASSWORD"),
            db=os.environ.get("MYSQL_DATABASE")
        )

        self.__cursor = self.__db.cursor()

    def get_non_end_id_and_sid(self):
        """
        is_endが0のidとsidをリストで取得
        """
            
        query = "SELECT id,sid FROM main_app_reservationparent WHERE is_end != 1"
        self.__cursor.execute(query)

        result = []

        for row in self.__cursor.fetchall():
            result.append({
                "id": row[0],
                "sid": row[1]
            })
        
        return result

    def __get_call_details(self, call_sid):
        """
        twilioサービスから通話情報の詳細を取得する関数
        call_detailsにある項目は取得可能
        """
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')

        client = Client(account_sid, auth_token)
        call = client.calls(call_sid).fetch()
        
        call_details = {
            "Call SID": call.sid,
            "From": call.from_formatted,
            "To": call.to_formatted,
            "Status": call.status,
            "Start Time": str(call.start_time),
            "End Time": str(call.end_time),
            "Duration": call.duration,
            "Price": call.price,
            "Price Unit": call.price_unit
        }

        return call_details
    
    def get_twilio_status(self, call_sid):
        details = self.__get_call_details(call_sid)
        return details["Status"]
    
    def __check_wait_status(self, parent_id):
        query = f"SELECT id, status FROM main_app_reservationchild WHERE `status` = 4 AND parent_id = '{parent_id}'"
        self.__cursor.execute(query)

        result = []

        for row in self.__cursor.fetchall():
            result.append({
                "id": row[0],
                "status": row[1]
            })
        
        return result
    

    def set_status(self, parent_id, twilio_status, title=None, message=None):
        """
        status引数をもとに、main_app_reservationchildに情報を追加する関数
        """
        wait_status = self.__check_wait_status(parent_id)
        if wait_status:
            for status in wait_status:
                delete_query = f"DELETE FROM main_app_reservationchild WHERE id = '{status['id']}'"
                self.__cursor.execute(delete_query)
                self.__db.commit()

        insert_query = (
            "INSERT INTO main_app_reservationchild (id, datetime, status, title, message, parent_id) "
            "VALUES (%s, %s, %s, %s, %s, %s)"
        )

        unique_id = str(uuid.uuid4()).replace('-', '')
        datetime_now = str(datetime.now())
        status = self.STATUS_INFO[twilio_status]["status"]

        if title:
            status_title = title
        else:
            status_title = self.STATUS_INFO[twilio_status]["title"]

        if message:
            status_message = message
        else:
            status_message = self.STATUS_INFO[twilio_status]["message"]

        insert_data = (
            unique_id,
            datetime_now,
            status,
            status_title, 
            status_message,
            parent_id,
        )

        self.__cursor.execute(insert_query, insert_data)

        self.__db.commit()
        
        return insert_data

    def change_parent_status(self, parent_id, error=False):
        """
        main_app_reservationparentのis_end statusを0から1へ変更する
        """
        insert_query = (
            "INSERT INTO main_app_reservationchild (id, datetime, status, title, message, parent_id) "
            "VALUES (%s, %s, %s, %s, %s, %s)"
        )
        
        if error:
            unique_id = str(uuid.uuid4()).replace('-', '')
            datetime_now = str(datetime.now())

            self.__cursor.execute(insert_query, (
                unique_id,
                datetime_now,
                self.STATUS_INFO["failed"]["status"],
                self.STATUS_INFO["failed"]["title"], 
                self.STATUS_INFO["failed"]["message"],
                parent_id,
            ))
        
        unique_id = str(uuid.uuid4()).replace('-', '')
        datetime_now = str(datetime.now())

        self.__cursor.execute(insert_query, (
            unique_id,
            datetime_now,
            self.END,
            "代理予約処理が完了しました", 
            "代理予約処理が完了しました。",
            parent_id,
        ))

        update_query = f"UPDATE main_app_reservationparent SET is_end=1 WHERE id='{parent_id}'"
        self.__cursor.execute(update_query)

        self.__db.commit()

        return True
    