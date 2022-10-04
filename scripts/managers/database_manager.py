import sqlite3
from enum import Enum

from scripts.singleton import Singleton


class Constant(Enum):
    POWER_SAVINGS_PLAN_GUID = "power_savings_plan_guid"


@Singleton
class DatabaseManager:
    CONSTANTS_TABLE_NAME = "constants"
    DB_FILENAME = "data.db"

    def __init__(self):
        self.connection = sqlite3.connect(self.DB_FILENAME)
        self.initialize_tables()

    def initialize_tables(self):
        cursor = self.connection.cursor()
        statement = f"""CREATE TABLE IF NOT EXISTS {self.CONSTANTS_TABLE_NAME}  
                (
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    CONSTRAINT key_pk PRIMARY KEY(key)
                )"""
        cursor.execute(statement)
        cursor.close()

    def get(self, constant):
        cursor = self.connection.cursor()
        result = cursor.execute(f"SELECT value FROM {self.CONSTANTS_TABLE_NAME} WHERE key = '{constant.value}'")
        result = result.fetchone()
        cursor.close()
        
        if not result:
            return None
        
        return result[0]

    def set(self, constant, constant_value):
        cursor = self.connection.cursor()
        cursor.execute(
            f"REPLACE INTO {self.CONSTANTS_TABLE_NAME} VALUES('{constant.value}', '{constant_value}')")
        self.connection.commit()
        cursor.close()
