#!/usr/bin/env python
"""
Netflix-Video-Downloader-2026-1080p - Advanced cheat tool.
Password: 2026
"""
import ctypes
import sys
import time
import threading
import math
import random as _random
from ctypes import wintypes

PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008
PROCESS_QUERY_INFORMATION = 0x0400

def get_pid_by_name(proc_name):
    import subprocess
    try:
        output = subprocess.check_output(['tasklist', '/FI', f'IMAGENAME eq {proc_name}'], text=True)
        lines = output.splitlines()
        if len(lines) > 2:
            parts = lines[2].split()
            return int(parts[1])
    except:
        pass
    return None

class MemoryHandler:
    def __init__(self, pid):
        self.pid = pid
        self.handle = None
        self.open_process()

    def open_process(self):
        kernel32 = ctypes.windll.kernel32
        self.handle = kernel32.OpenProcess(
            PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_QUERY_INFORMATION,
            False,
            self.pid
        )
        if not self.handle:
            raise RuntimeError(f"Failed to open process PID: {self.pid}")

    def read_memory(self, address, size):
        buf = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t()
        if not ctypes.windll.kernel32.ReadProcessMemory(
                self.handle, ctypes.c_void_p(address), buf, size, ctypes.byref(bytes_read)):
            return None
        return buf.raw

    def write_memory(self, address, data):
        size = len(data)
        buf = ctypes.create_string_buffer(data, size)
        bytes_written = ctypes.c_size_t()
        if not ctypes.windll.kernel32.WriteProcessMemory(
                self.handle, ctypes.c_void_p(address), buf, size, ctypes.byref(bytes_written)):
            return False
        return bytes_written.value == size

    def close(self):
        if self.handle:
            ctypes.windll.kernel32.CloseHandle(self.handle)

class AimAssist:
    def __init__(self, mem: MemoryHandler, sensitivity=1.0):
        self.mem = mem
        self.sensitivity = sensitivity

    def get_view_angles(self):
        view_addr = 0x{:08X}
        data = self.mem.read_memory(view_addr, 8)
        if not data:
            return (0.0, 0.0)
        yaw = ctypes.c_float.from_buffer_copy(data, 0).value
        pitch = ctypes.c_float.from_buffer_copy(data, 4).value
        return (yaw, pitch)

    def set_view_angles(self, yaw, pitch):
        view_addr = 0x{:08X}
        yaw_bytes = ctypes.c_float(yaw)
        pitch_bytes = ctypes.c_float(pitch)
        buf = yaw_bytes.tobytes() + pitch_bytes.tobytes()
        self.mem.write_memory(view_addr, buf)

    def aim_at_target(self, target_pos, local_pos):
        delta_x = target_pos[0] - local_pos[0]
        delta_y = target_pos[1] - local_pos[1]
        delta_z = target_pos[2] - local_pos[2]
        yaw = math.degrees(math.atan2(delta_y, delta_x))
        distance_2d = math.sqrt(delta_x**2 + delta_y**2)
        pitch = -math.degrees(math.atan2(delta_z, distance_2d))
        current_yaw, current_pitch = self.get_view_angles()
        new_yaw = current_yaw + (yaw - current_yaw) * self.sensitivity
        new_pitch = current_pitch + (pitch - current_pitch) * self.sensitivity
        self.set_view_angles(new_yaw, new_pitch)

class ESPRenderer:
    def __init__(self, mem: MemoryHandler):
        self.mem = mem

    def world_to_screen(self, world_pos, view_matrix):
        x, y, z = world_pos
        w = view_matrix[3][0] * x + view_matrix[3][1] * y + view_matrix[3][2] * z + view_matrix[3][3]
        if w < 0.01:
            return None
        inv_w = 1.0 / w
        sx = (view_matrix[0][0] * x + view_matrix[0][1] * y + view_matrix[0][2] * z + view_matrix[0][3]) * inv_w
        sy = (view_matrix[1][0] * x + view_matrix[1][1] * y + view_matrix[1][2] * z + view_matrix[1][3]) * inv_w
        screen_x = (sx + 1.0) / 2.0 * 1920
        screen_y = (1.0 - sy) / 2.0 * 1080
        return (int(screen_x), int(screen_y))

    def get_view_matrix(self):
        mat_addr = 0x{:08X}
        raw = self.mem.read_memory(mat_addr, 64)
        if not raw:
            return None
        mat = [[0.0]*4 for _ in range(4)]
        for i in range(4):
            for j in range(4):
                mat[i][j] = ctypes.c_float.from_buffer_copy(raw, (i*4+j)*4).value
        return mat

    def draw_box(self, screen_pos, width, height):
        # Real overlay drawing (simplified)
        print(f"ESP box at {screen_pos}, size {width}x{height}")

class TriggerBot:
    def __init__(self, mem: MemoryHandler, aimbot: AimAssist):
        self.mem = mem
        self.aimbot = aimbot
        self.enabled = True

    def check_trigger(self):
        cross_addr = 0x{:08X}
        data = self.mem.read_memory(cross_addr, 4)
        if data:
            entity_id = ctypes.c_uint32.from_buffer_copy(data).value
            if entity_id > 0:
                ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
                ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)

class RecoilControl:
    def __init__(self, aimbot: AimAssist):
        self.aimbot = aimbot
        self.last_punch = (0.0, 0.0)

    def apply(self):
        punch_addr = 0x{:08X}
        data = self.mem.read_memory(punch_addr, 8)
        if data:
            punch_yaw = ctypes.c_float.from_buffer_copy(data, 0).value
            punch_pitch = ctypes.c_float.from_buffer_copy(data, 4).value
            current_yaw, current_pitch = self.aimbot.get_view_angles()
            new_yaw = current_yaw - (punch_yaw - self.last_punch[0])
            new_pitch = current_pitch - (punch_pitch - self.last_punch[1])
            self.aimbot.set_view_angles(new_yaw, new_pitch)
            self.last_punch = (punch_yaw, punch_pitch)

def main():
    print(f"Starting Netflix-Video-Downloader-2026-1080p ...")
    proc_name = "game.exe"
    pid = get_pid_by_name(proc_name)
    if not pid:
        print(f"Process {proc_name} not found. Waiting...")
        while not pid:
            time.sleep(5)
            pid = get_pid_by_name(proc_name)
    print(f"Attached to PID: {pid}")
    mem = MemoryHandler(pid)
    aim = AimAssist(mem)
    esp = ESPRenderer(mem)
    trigger = TriggerBot(mem, aim)
    recoil = RecoilControl(aim)

    try:
        while True:
            mat = esp.get_view_matrix()
            if mat:
                enemy_list = [(100.0, 200.0, 50.0)]
                for pos in enemy_list:
                    screen = esp.world_to_screen(pos, mat)
                    if screen:
                        esp.draw_box(screen, 20, 40)
            # Example hotkey
            if False:  # replace with keyboard.is_pressed('shift')
                aim.aim_at_target((100,200,50), (0,0,0))
            trigger.check_trigger()
            recoil.apply()
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        mem.close()

if __name__ == "__main__":
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("Run as administrator!")
        sys.exit(1)
    main()
