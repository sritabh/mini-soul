import gc
import os

# --- ESP32 RAM ---
gc.collect()
ram_free = gc.mem_free()
ram_used = gc.mem_alloc()
ram_total = ram_free + ram_used

print("=== ESP32 Memory ===")
print("RAM Free:  {} bytes ({} KB)".format(ram_free, ram_free // 1024))
print("RAM Used:  {} bytes ({} KB)".format(ram_used, ram_used // 1024))
print("RAM Total: {} bytes ({} KB)".format(ram_total, ram_total // 1024))

# --- Flash Storage ---
fs = os.statvfs('/')
block_size  = fs[0]
total_blocks = fs[2]
free_blocks  = fs[3]

flash_total = block_size * total_blocks
flash_free  = block_size * free_blocks
flash_used  = flash_total - flash_free

print("\n=== Flash Storage ===")
print("Flash Free:  {} bytes ({} KB)".format(flash_free, flash_free // 1024))
print("Flash Used:  {} bytes ({} KB)".format(flash_used, flash_used // 1024))
print("Flash Total: {} bytes ({} KB)".format(flash_total, flash_total // 1024))
