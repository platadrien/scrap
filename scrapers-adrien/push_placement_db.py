# from app import get_db_connection
import os, json, psycopg2, random
from datetime import datetime


def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="api_alpha",
        user="postgres",
        password="postgres",
    )
    return conn


def push_wine(data, année):
    conn = get_db_connection()
    cursor = conn.cursor()
    print(année)
    for table, values in data.items():
        if table == "placement":
            name = (
                values["Appellation :"]
                + " "
                + values["Domaine :"]
                + " "
                + values["Proprietaire :"]
                + " "
                + values["Couleur :"]
                + " "
                + année
            )
            item_count = random.randint(1, 21)
            type = "vin"
            active = True
            cursor.execute(f"""SELECT id FROM placement WHERE name = '{name}'""")
            exist = cursor.fetchone()
            if not exist:
                cursor.execute(
                    "INSERT INTO placement VALUES (nextval('placement_id_seq'), %s, %s, %s, %s, %s)",
                    (type, item_count, json.dumps(values), name, active),
                )
                conn.commit()
            cursor.execute("SELECT id FROM {0} WHERE name='{1}';".format(table, name))
            id = cursor.fetchone()

        elif table == "price":

            for v in values:
                placement = str(id[0])
                print(placement)
                if v["year"] == 2022:
                    date = datetime(
                        year=int(v["year"]), month=11, day=random.randint(1, 30)
                    )
                else:
                    date = datetime(
                        year=int(v["year"]),
                        month=random.randint(1, 12),
                        day=random.randint(1, 29),
                    )

                sql = "INSERT INTO placement_price (id_placement,date,price,currency) VALUES ({0}, '{1}', {2}, 'EUR');".format(
                    placement, date.strftime("%Y-%m-%d %H:%M:%S"), v["price"]
                )

                print(sql)
                cursor.execute(sql)
                conn.commit()


if __name__ == "__main__":

    for file in os.listdir("./JSON_PRICE"):
        année = file[:4]
        with open("./JSON_PRICE/" + file, "r") as f:

            push_wine(json.load(f), année)
