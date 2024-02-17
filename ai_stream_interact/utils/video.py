from pygrabber.dshow_graph import FilterGraph


def get_available_cameras():

    devices = FilterGraph().get_input_devices()

    available_cameras = {}

    for device_index, device_name in enumerate(devices):
        available_cameras[device_index] = device_name

    return available_cameras


print(get_available_cameras())
