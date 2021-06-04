from mpu6050 import mpu6050
import Adafruit_BMP.BMP085 as BMP085

import smbus  # import SMBus module of I2C
import time
from datetime import datetime
import math
import statistics
import psycopg2

mpu = mpu6050(0x68)  # MPU6050 sensor
sensor = BMP085.BMP085()  # BMP085 sensor

# some MPU6050 Registers and their Address
Register_A = 0  # Address of Configuration register A
Register_B = 0x01  # Address of configuration register B
Register_mode = 0x02  # Address of mode register

X_axis_H = 0x03  # Address of X-axis MSB data register
Z_axis_H = 0x05  # Address of Z-axis MSB data register
Y_axis_H = 0x07  # Address of Y-axis MSB data register
declination = 0.0902  #-0.00669  # define declination angle of location where measurement going to be done
pi = 3.14159265359  # define pi value


def Magnetometer_Init():
    # write to Configuration Register A
    bus.write_byte_data(Device_Address, Register_A, 0x70)

    # Write to Configuration Register B for gain
    bus.write_byte_data(Device_Address, Register_B, 0xa0)

    # Write to mode Register for selecting mode
    bus.write_byte_data(Device_Address, Register_mode, 0)
def read_raw_data(addr):
    # Read raw 16-bit value
    high = bus.read_byte_data(Device_Address, addr)
    low = bus.read_byte_data(Device_Address, addr + 1)

    # concatenate higher and lower value
    value = ((high << 8) | low)

    # to get signed value from module
    if (value > 32768):
        value = value - 65536
    return value

bus = smbus.SMBus(1)  # or bus = smbus.SMBus(0) for older version boards
Device_Address = 0x1e  # HMC5883L magnetometer device address

Magnetometer_Init()  # initialize HMC5883L magnetometer

# DATABAZA
dsn = "host={} dbname={} user={} password={}".format("147.175.106.248", "db_valko", "valko", "2020v605")
conn = psycopg2.connect(dsn)

MPU6050_id = 1
HMC5883L_id = 2
BMP085_id = 3


def delete_data():
    cur = conn.cursor()
    sql = "DROP TABLE senzory,meranie,namerana_hodnota"
    cur.execute(sql)
    sql = "CREATE TABLE senzory (id_senzor SERIAL PRIMARY KEY,senzor VARCHAR(25) NOT NULL,popis VARCHAR (255))"
    cur.execute(sql)
    sql = "CREATE TABLE meranie (id_merania SERIAL PRIMARY KEY,cas TIMESTAMP)"
    cur.execute(sql)
    sql = "CREATE TABLE namerana_hodnota (id SERIAL PRIMARY KEY,id_senzor INTEGER NOT NULL, FOREIGN KEY (id_senzor)REFERENCES senzory (id_senzor) ON UPDATE CASCADE ON DELETE CASCADE, velicina VARCHAR(255) NOT NULL , hodnota DECIMAL(30,14), id_merania INTEGER NOT NULL, FOREIGN KEY (id_merania)REFERENCES meranie (id_merania) ON UPDATE CASCADE ON DELETE CASCADE )"
    cur.execute(sql)
    sql = "INSERT INTO senzory (senzor,popis) VALUES ('MPU6050','Senzor obsahuje gyroskop aj akcelerometer') RETURNING id_senzor"
    cur.execute(sql)
    MPU6050_id = cur.fetchone()[0]
    sql = "INSERT INTO senzory (senzor,popis) VALUES ('HMC5883L','je viaccipovy modul urceny na snimanie magnetickeho pola') RETURNING id_senzor"
    cur.execute(sql)
    HMC5883L_id = cur.fetchone()[0]
    sql = "INSERT INTO senzory (senzor,popis) VALUES ('BMP085','snimac navrhnuty na nameranie atmosferickeho tlaku') RETURNING id_senzor"
    cur.execute(sql)
    BMP085_id = cur.fetchone()[0]
    conn.commit()
    cur.close()

delete_data()

cur = conn.cursor()
mod = -1
mod_arr = []
cnt = 0
sleep = 0.001
mpu.set_accel_range(0x10)
while True:


    now = datetime.now()
    dt_string = now.strftime('%d-%m-%Y %H:%M:%S')
    cur.execute("INSERT INTO meranie (cas) VALUES (%s) RETURNING id_merania;", (dt_string,))
    id_merania = cur.fetchone()[0]
    print("Meranie: "+ str(id_merania))


    #id = cur.fetchone()[0]

    print("Accelerometer data")
    accel_data = mpu.get_accel_data()
    #accel_data['x'] = accel_data['x'] / 16384
    #accel_data['y'] = accel_data['y'] / 16384
    #accel_data['z'] = accel_data['z'] / 16384
    print("X: " + str(accel_data['x']) + "  Y: " + str(accel_data['y']) + "  Z: " + str(accel_data['z']+0.1))

    print("Gyroscope data")
    gyro_data = mpu.get_gyro_data()
    gyro_data['x'] = gyro_data['x'] / 131
    gyro_data['y'] = gyro_data['y'] / 131
    gyro_data['z'] = gyro_data['z'] / 131
    print("X: " + str(gyro_data['x']) + "  Y: " + str(gyro_data['y']) + "  Z: " + str(gyro_data['z']))


    cur.execute("INSERT INTO namerana_hodnota (id_senzor,velicina,hodnota,id_merania) VALUES (%s,%s,%s,%s)", (MPU6050_id, 'akcel_x', accel_data['x'], id_merania))
    cur.execute("INSERT INTO namerana_hodnota (id_senzor,velicina,hodnota,id_merania) VALUES (%s,%s,%s,%s)", (MPU6050_id, 'akcel_y', accel_data['y'], id_merania))
    cur.execute("INSERT INTO namerana_hodnota (id_senzor,velicina,hodnota,id_merania) VALUES (%s,%s,%s,%s)", (MPU6050_id, 'akcel_z', accel_data['z']+0.1, id_merania))

    cur.execute("INSERT INTO namerana_hodnota (id_senzor,velicina,hodnota,id_merania) VALUES (%s,%s,%s,%s)",(MPU6050_id, 'gyro_x', gyro_data['x'], id_merania))
    cur.execute("INSERT INTO namerana_hodnota (id_senzor,velicina,hodnota,id_merania) VALUES (%s,%s,%s,%s)",(MPU6050_id, 'gyro_y', gyro_data['y'], id_merania))
    cur.execute("INSERT INTO namerana_hodnota (id_senzor,velicina,hodnota,id_merania) VALUES (%s,%s,%s,%s)",(MPU6050_id, 'gyro_z', gyro_data['z'], id_merania))

    #print("Temp : " + str(mpu.get_temp()))
    print("-------------------------------")
    # Read Accelerometer raw value
    x = read_raw_data(X_axis_H)
    z = read_raw_data(Z_axis_H)
    y = read_raw_data(Y_axis_H)
    heading = math.atan2(y, x) + declination
    # Due to declination check for >360 degree
    if (heading > 2 * pi):
        heading = heading - 2 * pi
    # check for sign
    if (heading < 0):
        heading = heading + 2 * pi

    # convert into angle
    heading_angle = int(heading * 180 / pi)

    cur.execute("INSERT INTO namerana_hodnota (id_senzor,velicina,hodnota,id_merania) VALUES (%s,%s,%s,%s)",(HMC5883L_id, 'magnet_x', x, id_merania))
    cur.execute("INSERT INTO namerana_hodnota (id_senzor,velicina,hodnota,id_merania) VALUES (%s,%s,%s,%s)",(HMC5883L_id, 'magnet_y', y, id_merania))
    cur.execute("INSERT INTO namerana_hodnota (id_senzor,velicina,hodnota,id_merania) VALUES (%s,%s,%s,%s)",(HMC5883L_id, 'magnet_z', z, id_merania))

    cur.execute("INSERT INTO namerana_hodnota (id_senzor,velicina,hodnota,id_merania) VALUES (%s,%s,%s,%s)",(HMC5883L_id, 'kurz', heading_angle, id_merania))
    print("Magnetic field sensor data")
    print("X = %d Y = %d Z = %d" % (x, y, z))
    print("Heading Angle = %d°" % heading_angle)
    print("-------------------------------")
    print("Barometer data")
    #print('Temp = {0:0.2f} *C'.format(sensor.read_temperature()))
    print('Pressure = {0:0.2f} hPa'.format(sensor.read_pressure()/100))
    print('Altitude = {0:0.2f} m'.format(sensor.read_altitude()))
    #print('Sealevel Pressure = {0:0.2f} Pa'.format(sensor.read_sealevel_pressure()))
    print()
    cur.execute("INSERT INTO namerana_hodnota (id_senzor,velicina,hodnota,id_merania) VALUES (%s,%s,%s,%s)",(BMP085_id, 'tlak', format(sensor.read_pressure()/100), id_merania))
    cur.execute("INSERT INTO namerana_hodnota (id_senzor,velicina,hodnota,id_merania) VALUES (%s,%s,%s,%s)",(BMP085_id, 'nadmor. vyska', format(sensor.read_altitude()), id_merania))



    if accel_data['z'] + 0.1 < -1.25 or accel_data['z'] + 0.1 > -0.75:
            mpu.set_accel_range(0x00)
            cnt = 0
            mod = 0
            sleep = 0.001
    else:
        cnt += 1
        #stav 'klud'
        if cnt == 25:
            mpu.set_accel_range(0x10)
            mod = -1
            sleep = 0.05

    if id_merania == 1:
        mod_arr.append(-1)
    else:
        mod_arr.append(mod)




    conn.commit()
    #cur.close()
    time.sleep(sleep)
