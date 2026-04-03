
import asyncio
import traceback
import csv
import datetime
import sqlite3
from pathlib import Path
from pymodbus.client import AsyncModbusTcpClient

IMO_NO = "1114389"

#CSV_LOG_PREFIX = "/home/drums/csv/H429_"
CSV_LOG_PREFIX = "H429_"




DG1_IP = "192.168.18.26"
DG1_SLAVE_ID = 16
DG1_Name = "DG#1"
DG1_SerialNo = "DE618Z5178"




LIVE_DB_PATH = Path(__file__).resolve().parent / "live_engine_data.db"
LIVE_DATA_STORE = None


class LiveDataStore:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=DELETE;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self.conn.execute("PRAGMA busy_timeout=5000;")
        self._ensure_schema()
        self.conn.commit()

    def _ensure_schema(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS live_engine_data (
                imo INTEGER,
                serial TEXT,
                addr TEXT,
                label TEXT,
                timestamp DATETIME,
                val REAL,
                unit TEXT
            );
            """
        )
        self.conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_live_engine_data_key
            ON live_engine_data (imo, serial, addr);
            """
        )

    def upsert(self, imo, serial, addr, label, timestamp, val, unit):
        self.conn.execute(
            """
            INSERT INTO live_engine_data (imo, serial, addr, label, timestamp, val, unit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(imo, serial, addr) DO UPDATE SET
                label = excluded.label,
                timestamp = excluded.timestamp,
                val = excluded.val,
                unit = excluded.unit;
            """,
            (imo, serial, str(addr), label, timestamp, val, unit),
        )

    def close(self):
        self.conn.commit()
        self.conn.close()

    def flush(self):
        self.conn.commit()


def write_measurement(writer, imo, serial, addr, label, timestamp, val, unit):
    if str(serial).strip() == "" or str(label).strip() == "" or str(addr).strip() == "":
        return
    writer.writerow([imo, serial, addr, label, timestamp, val, unit])
    if LIVE_DATA_STORE is not None:
        LIVE_DATA_STORE.upsert(imo, serial, addr, label, timestamp, val, unit)




# ------------------- Read MODBUS DATAa & Write LOG CSV -------------------

async def read_modbus_data_DG(DG, slave_id, dg_name, imo, serial):
    try:
        flag = False
        dt = datetime.datetime.now(datetime.timezone.utc)
        timestamp_iso = dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        logfile = f"{CSV_LOG_PREFIX}{dg_name.replace('#','')}-{dt:%Y-%m-%d-%H-%M-%S}.csv"

        with open(logfile, "a", newline="") as f:
            writer = csv.writer(f)

            # ========== ANALOG ==========
            print(f"\n🧭 {dg_name} Analog Signal")
            analog_map = {
                #0x01: (f"{dg_name} FUEL OIL TEMPERATURE ENGINE INLET", "deg C", 1),
                #0x02: (f"{dg_name} BOOST AIR TEMPERATURE", "deg C", 1),
                0x03: (f"{dg_name} LUB OIL TEMPERATURE ENGINE INLET", "deg C", 1),
                0x04: (f"{dg_name} H.T. WATER TEMPERATURE ENGINE OUTLET", "deg C", 1),
                #0x05: (f"{dg_name} H.T. WATER TEMPERATURE ENGINE INLET", "deg C", 1),
                0x06: (f"{dg_name} No.1CYL. EXHAUST GAS TEMPERATURE", "deg C", 1),
                0x07: (f"{dg_name} No.2CYL. EXHAUST GAS TEMPERATURE", "deg C", 1),
                0x08: (f"{dg_name} No.3CYL. EXHAUST GAS TEMPERATURE", "deg C", 1),
                0x09: (f"{dg_name} No.4CYL. EXHAUST GAS TEMPERATURE", "deg C", 1),
                0x0A: (f"{dg_name} No.5CYL. EXHAUST GAS TEMPERATURE", "deg C", 1),
                0x0B: (f"{dg_name} No.6CYL. EXHAUST GAS TEMPERATURE", "deg C", 1),
                0x0E: (f"{dg_name} EXHAUST GAS TEMPERATURE T/C INLET 1", "deg C", 1),
                0x0F: (f"{dg_name} EXHAUST GAS TEMPERATURE T/C INLET 2", "deg C", 1),
                0x10: (f"{dg_name} EXHAUST GAS TEMPERATURE T/C OUTLET", "deg C", 1),
                0x11: (f"{dg_name} H.T. WATER PRESSURE ENGINE INLET", "MPa", 0.01),
                #0x12: (f"{dg_name} BOOST AIR PRESSURE", "MPa", 0.01),
                0x13: (f"{dg_name} L.T. WATER PRESSURE ENGINE INLET", "MPa", 0.01),
                0x14: (f"{dg_name} STARTING AIR PRESSURE", "MPa", 0.01),
                0x15: (f"{dg_name} FUEL OIL PRESSURE ENGINE INLET", "MPa", 0.01),
                #0x16: (f"{dg_name} CONTROL AIR PRESSURE", "MPa", 0.01),
                #0x17: (f"{dg_name} LO PRESS T/C INLET", "MPa", 0.01),
                #0x18: (f"{dg_name} LUB OIL FILTER DIFFERENTIAL PRESSURE", "MPa", 0.01),
                0x19: (f"{dg_name} LUB OIL PRESSURE", "MPa", 0.01),
                0x1A: (f"{dg_name} ENGINE SPEED", "min-1", 1),
                0x1C: (f"{dg_name} LOAD", "kW", 1),
                0x1D: (f"{dg_name} RUNNING HOUR", "x10Hours", 1),
                #0x21: (f"{dg_name} LUB. OIL TEMP. ENGINE OUTLET", "deg C", 1),
                #0x22: (f"{dg_name} L.T. WATER TEMP. ENGINE INLET", "deg C", 1),
                #0x23: (f"{dg_name} L.T. WATER TEMP. ENGINE OUTLET", "deg C", 1),
                #0x31: (f"{dg_name} T/C SPEED", "min-1", 1),
            }

            resp = await DG.read_input_registers(0x00, 35, slave=slave_id)
            if not resp.isError():
                for i, reg in enumerate(resp.registers):
                    addr = 0x00 + i
                    raw_val = int(reg)

                    if addr in analog_map:
                        label, unit, ratio = analog_map[addr]
                        val = raw_val * ratio

                        print(f"📈 {label:<50}: {val} {unit}")
                        write_measurement(
                            writer,
                            imo,
                            serial,
                            addr + 40000,
                            label,
                            timestamp_iso,
                            val,
                            unit,
                        )

            else:
                print(f"❌ Error reading analog registers from {dg_name}")
                flag = True


            # ---------------- DISCRETE ----------------
            print(f"\n🧭 {dg_name} Digital Signal")
            discrete_map = {
                0x01: (f"{dg_name} LUB OIL FILTER DIFFERENTIAL PRESSURE HIGH", "On/Off",),
                0x02: (f"{dg_name} CONTROL AIR PRESSURE LOW", "On/Off",),
                0x03: (f"{dg_name} FUEL OIL PRESSURE LOW", "On/Off",),
                0x04: (f"{dg_name} LUB OIL PRESSURE LOW", "On/Off",),
                0x05: (f"{dg_name} H.T. WATER PRESSURE LOW", "On/Off",),
                0x06: (f"{dg_name} L.T. WATER PRESSURE LOW", "On/Off",),
                0x07: (f"{dg_name} FUEL OIL DRAIN LEVEL HIGH", "On/Off",),
                0x08: (f"{dg_name} H.T. WATER TEMPERATURE HIGH", "On/Off",),
                0x09: (f"{dg_name} T/C LUB OIL PRESSURE LOW", "On/Off",),
                0x0A: (f"{dg_name} FUEL OIL FILTER DIFFERENTIAL PRESSURE HIGH", "On/Off",),
                0x0B: (f"{dg_name} STARTING AIR PRESSURE LOW", "On/Off",),
                0x0C: (f"{dg_name} FUEL OIL LEAK TANK LEVEL HIGH", "On/Off",),
                0x0D: (f"{dg_name} LUB OIL SUMP TANK LEVEL LOW", "On/Off",),
                0x0E: (f"{dg_name} LUB OIL SUMP TANK LEVEL HIGH", "On/Off",),
                0x0F: (f"{dg_name} OIL MIST PRE-ALARM", "On/Off",),
                0x10: (f"{dg_name} OIL MIST DETECTOR TROUBLE", "On/Off",),
                0x11: (f"{dg_name} ENGINE RUN", "On/Off",),
                0x12: (f"{dg_name} READY TO START", "On/Off",),
                0x13: (f"{dg_name} OVER SPEED (STOP)", "On/Off",),
                0x14: (f"{dg_name} H.T. WATER TEMPERATURE HIGH (STOP)", "On/Off",),
                0x15: (f"{dg_name} LUB OIL PRESSURE LOW (STOP)", "On/Off",),
                0x16: (f"{dg_name} OIL MIST HIGH DENSITY ALARM (STOP)", "On/Off",),
                0x17: (f"{dg_name} EMERGENCY STOP (REMOTE/LOCAL)", "On/Off",),
                0x18: (f"{dg_name} START FAILURE", "On/Off",),
                0x19: (f"{dg_name} PRIMING PUMP TERMAL FAILURE", "On/Off",),
                0x1A: (f"{dg_name} PRIMING LUB OIL PRESSURE LOW", "On/Off",),
                0x1B: (f"{dg_name} PRIMING PUMP RUN", "On/Off",),

                0x21: (f"{dg_name} SYSTEM FAILURE", "On/Off",),
                0x22: (f"{dg_name} CONTROL MODULE FAILURE", "On/Off",),
                0x23: (f"{dg_name} SAFTY MODULE FAILURE", "On/Off",),
                0x24: (f"{dg_name} LINK TO ENGINE CONDITION DISPLAY FAILURE", "On/Off",),
                0x25: (f"{dg_name} LINK TO REMOTE I/O 1 FAILURE", "On/Off",),
                0x26: (f"{dg_name} LINK TO REMOTE I/O 2 FAILURE", "On/Off",),
                0x27: (f"{dg_name} LINK TO LCD GAGE BOARD FAILURE", "On/Off",),

                0x29: (f"{dg_name} No.1 ALARM REPOSE SIGNAL(#14)", "On/Off",),
                0x2A: (f"{dg_name} No.2 ALARM REPOSE SIGNAL(#14T)", "On/Off",),
                0x2B: (f"{dg_name} No.3 ALARM REPOSE SIGNAL(EXH. GAS)", "On/Off",),
                0x2C: (f"{dg_name} No.4 ALARM REPOSE SIGNAL(PRIMING)", "On/Off",),
                0x2D: (f"{dg_name} No.5 ALARM REPOSE SIGNAL(STARTING)", "On/Off",),
                0x2E: (f"{dg_name} No.6 ALARM REPOSE SIGNAL(FILTER DIFF. PRESS.)", "On/Off",),

                0x31: (f"{dg_name} No.1CYL. EXH. GAS TEMP. DEVIATION ALARM", "On/Off",),
                0x32: (f"{dg_name} No.2CYL. EXH. GAS TEMP. DEVIATION ALARM", "On/Off",),
                0x33: (f"{dg_name} No.3CYL. EXH. GAS TEMP. DEVIATION ALARM", "On/Off",),
                0x34: (f"{dg_name} No.4CYL. EXH. GAS TEMP. DEVIATION ALARM", "On/Off",),
                0x35: (f"{dg_name} No.5CYL. EXH. GAS TEMP. DEVIATION ALARM", "On/Off",),
                0x36: (f"{dg_name} No.6CYL. EXH. GAS TEMP. DEVIATION ALARM", "On/Off",),

                0x39: (f"{dg_name} EXH. GAS TEMP. DEVIATION ALARM(COMMON)", "On/Off",),

                0x3B: (f"{dg_name} EMERGENCY STOP SWITCH OF EXT. (DISCONNECTION)", "On/Off",),
                0x3C: (f"{dg_name} EMERGENCY STOP SWITCH ON ECD (DISCONNECTION)", "On/Off",),
                0x3D: (f"{dg_name} H.T. WATER TEMP. HIGH SWITCH (DISCONNECTION)", "On/Off",),
                0x3E: (f"{dg_name} LUB OIL PRESS. LOW SWITCH (DISCONNECTION)", "On/Off",),
                0x3F: (f"{dg_name} OILMIST DETECTOR HIGH-ALARM (DISCONNECTION)", "On/Off",),
                0x40: (f"{dg_name} EMERGENCY STOP SOLENOID (DISCONNECTION)", "On/Off",),

                0x41: (f"{dg_name} FUEL OIL TEMP. ENGINE INLET SENSOR FAILURE", "On/Off",),
                0x42: (f"{dg_name} BOOST AIR TEMP. SENSOR FAILURE", "On/Off",),
                0x43: (f"{dg_name} LUB OIL TEMP. ENGINE INLET SENSOR FAILURE", "On/Off",),
                0x44: (f"{dg_name} H.T. WATER TEMP. ENGINE OUTLET SENSOR FAILURE", "On/Off",),
                0x45: (f"{dg_name} H.T. WATER TEMP. ENGINE INLET SENSOR FAILURE", "On/Off",),
                0x46: (f"{dg_name} No.1CYL. EXH. GAS TEMP. SENSOR FAILURE", "On/Off",),
                0x47: (f"{dg_name} No.2CYL. EXH. GAS TEMP. SENSOR FAILURE", "On/Off",),
                0x48: (f"{dg_name} No.3CYL. EXH. GAS TEMP. SENSOR FAILURE", "On/Off",),
                0x49: (f"{dg_name} No.4CYL. EXH. GAS TEMP. SENSOR FAILURE", "On/Off",),
                0x4A: (f"{dg_name} No.5CYL. EXH. GAS TEMP. SENSOR FAILURE", "On/Off",),
                0x4B: (f"{dg_name} No.6CYL. EXH. GAS TEMP. SENSOR FAILURE", "On/Off",),

                0x4E: (f"{dg_name} EXH. GAS TEMP. T/C INLET 1 SENSOR FAILURE", "On/Off",),
                0x4F: (f"{dg_name} EXH. GAS TEMP. T/C INLET 2 SENSOR FAILURE", "On/Off",),
                0x50: (f"{dg_name} EXH. GAS TEMP. T/C OUTLET SENSOR FAILURE", "On/Off",),

                0x51: (f"{dg_name} H.T. WATER PRESS. INLET SENSOR FAILURE", "On/Off",),
                0x52: (f"{dg_name} BOOST AIR PRESS. SENSOR FAILURE", "On/Off",),
                0x53: (f"{dg_name} L.T. WATER PRESS. INLET SENSOR FAILURE", "On/Off",),
                0x54: (f"{dg_name} STARTING AIR PRESS SENSOR FAILURE", "On/Off",),
                0x55: (f"{dg_name} FO PRESS INLET SENSOR FAILURE", "On/Off",),
                0x56: (f"{dg_name} CONTROL AIR PRESS SENSOR FAILURE", "On/Off",),
                0x57: (f"{dg_name} LO PRESS T/C INLET SENSOR FAILURE", "On/Off",),
                0x58: (f"{dg_name} LUB OIL FILTER DIFF. PRESS. SENSOR FAILURE", "On/Off",),
                0x59: (f"{dg_name} LUB OIL PRESSURE SENSOR FAILURE", "On/Off",),
                0x5A: (f"{dg_name} ALL SPEED PICKUP SENSOR FAILURE", "On/Off",),
                0x5B: (f"{dg_name} LOAD INPUT FAILURE", "On/Off",),

                0x71: (f"{dg_name} LUB OIL TEMP. ENGINE OUTLET SENSOR FAILURE", "On/Off",),
                0x72: (f"{dg_name} L.T. WATER TEMP. ENGINE INLET SENSOR FAILURE", "On/Off",),
                0x73: (f"{dg_name} L.T. WATER TEMP. ENGINE OUTLET SENSOR FAILURE", "On/Off",),
                0x81: (f"{dg_name} T/C SPEED SENSOR FAILURE", "On/Off",),
            }
            resp = await DG.read_discrete_inputs(0x00, 0x81, slave=slave_id)  # read 129 bits (0x00â€“0x80)
            if not resp.isError():
                for i, bit in enumerate(resp.bits):
                    addr = 0x00 + i
                    if addr in discrete_map:
                        label, unit = discrete_map[addr]
                        val = int(bit)
                        print(f"🔹 {label:<55}: {val}")
                        write_measurement(
                            writer,
                            imo,
                            serial,
                            addr,
                            label,
                            timestamp_iso,
                            val,
                            unit,
                        )
            else:
                print(f"❌ Error reading Digital registers from {dg_name}")
                flag = True
        if flag == False:
            print(f"\n✅ WRITE {dg_name} DATA TO CSV SUCCESSFULLY")

    except Exception as e:
        print(f"❌ Error in read_modbus_data for {dg_name}: {e}")
        traceback.print_exc()
        await asyncio.sleep(0.1)

async def connect_client(client, address, retries=2, timeout=2, delay=1):
    """
    Try to connect to a client with limited retries.
    Returns True if connected, False if not.
    """
    for attempt in range(1, retries + 1):
        print(f"🔌 Connecting to {address} (try {attempt}/{retries})...")
        try:
            await asyncio.wait_for(client.connect(), timeout=timeout)
        except asyncio.TimeoutError:
            print(f"⏳ Timeout: {address} did not respond in {timeout}s")
        except Exception as e:
            print(f"❌ Connect error to {address}: {e}")

        if client.connected:
            print(f"✅ Connected {address}")
            return True

        await asyncio.sleep(delay)  # wait before retry

    print(f"⚠️ Could not connect to {address} after {retries} tries -> skip")
    return False


async def monitor_connection(client, address, retries=2, timeout=3):
    """
    Monitor client connection in background.
    If disconnected, retry connect with backoff.
    """
    backoff = 1
    while True:
        if not client.connected:
            print(f"🔁 Lost {address}, reconnecting...")

            ok = await connect_client(client, address, retries=retries, timeout=timeout, delay=backoff)
            if not ok:
                backoff = min(backoff * 2, 30)  # exponential backoff up to 30s
            else:
                backoff = 1  # reset backoff if reconnected
        await asyncio.sleep(0.5)


async def main():
    # Initialize clients
    global LIVE_DATA_STORE
    LIVE_DATA_STORE = LiveDataStore(LIVE_DB_PATH)

    DG1 = AsyncModbusTcpClient(DG1_IP, timeout=5)

    clients = [
        (DG1, DG1_IP, read_modbus_data_DG, (DG1_SLAVE_ID, DG1_Name, IMO_NO, DG1_SerialNo)),
    ]

    try:
        # Initialize monitor
        for client, ip, _, _ in clients:
            if await connect_client(client, ip):
                asyncio.create_task(monitor_connection(client, ip))

        # Read data
        while True:
            for client, ip, reader_func, args in clients:
                if client.connected:
                    try:
                        await reader_func(client, *args)
                        if LIVE_DATA_STORE is not None:
                            LIVE_DATA_STORE.flush()
                    except Exception as e:
                        print(f"❌ Error reading {ip}: {e}")
                        traceback.print_exc()
            print("\n⏱️ WAITING 2s")
            await asyncio.sleep(2)

    finally:
        print("🛑 Closing clients...")
        for client, _, _, _ in clients:
            await client.close()
        if LIVE_DATA_STORE is not None:
            LIVE_DATA_STORE.close()
        print("✅ All clients closed.")


if __name__ == "__main__":
    asyncio.run(main())

