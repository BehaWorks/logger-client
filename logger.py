import json
import uuid
from pprint import pprint

import swagger_client
import time
from swagger_client.rest import ApiException

import triad_openvr as vr

sid_length = 16


def transform_movements(data, sid, controller):
    rtn = []

    for timestamp, x, y, z, yaw, pitch, roll, r_x, r_y, r_z in zip(data["time"], data['x'], data['y'], data['z'],
                                                                   data['yaw'], data['pitch'], data['roll'],
                                                                   data['r_x'], data['r_y'], data['r_z']):
        movements.append({
            "session_id": sid,
            "timestamp": timestamp,
            "controller_id": controller,
            "x": x,
            "y": y,
            "z": z,
            "yaw": yaw,
            "pitch": pitch,
            "roll": roll,
            "r_x": r_x,
            "r_y": r_y,
            "r_z": r_z
        })

    return rtn


def trigger_pressed(device):
    return device.get_controller_inputs()['trigger'] > 0


def sample(device, num_samples, sample_rate):
    interval = 1 / sample_rate
    poses = vr.pose_sample_buffer()
    input_states = []
    sample_start = time.time()
    i = 0
    while trigger_pressed(v.devices["controller_2"]) or trigger_pressed(v.devices["controller_1"]):
        start = time.time()
        pose = vr.get_pose(device.vr)
        poses.append(pose[device.index].mDeviceToAbsoluteTracking, time.time() - sample_start)
        input_states.append(device.get_controller_inputs())
        input_states[i]['timestamp'] = time.time() - sample_start
        print(input_states[i]['trigger'])
        i += 1
        sleep_time = interval - (time.time() - start)
        if sleep_time > 0:
            time.sleep(sleep_time)
    return poses, input_states


try:
    v = vr.triad_openvr()

    while not (trigger_pressed(v.devices["controller_2"]) or trigger_pressed(v.devices["controller_1"])):
        print('waiting for input... %f' % v.devices["controller_2"].get_controller_inputs()['trigger'])
        time.sleep(0.1)

    data, buttons = sample(v.devices["controller_2"], 150, 60)
except:
    print('VR error, using example data...')
    f = open('example_movements.json', 'r')
    data = json.load(f)
    f = open("example_buttons.json", "r")
    buttons = json.load(f)
    f.close()

api_client = swagger_client.LoggerApi()

# f = open("vr_data.json", "w")
# json.dump(data.__dict__, f)
# f.close()
# f = open("buttons.json", "w")
# json.dump(buttons, f)
# f.close()
sid = uuid.uuid4().hex[0:sid_length]
movements = transform_movements(data, sid, "controller_2")
print(movements)

try:
    api_client.api_client.configuration.host = "https://team12-19.studenti.fiit.stuba.sk/api"
    api_response = api_client.post_logger_record(payload={"movements": movements, "buttons": buttons})
    pprint(api_response)
except ApiException as e:
    print("Exception when calling LoggerApi->post_logger_record: %s\n" % e)
