import tkinter as tk

class ScanlineLabel(tk.Label):
    """A custom label with animated scanline effect."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.scanline_pos = 0
        self.scan_direction = 1
        self.scan_speed = 3
        self.animate_scanline()
        
    def animate_scanline(self):
        # Create temporary label for size calculation
        temp = tk.Label(self.master, text=self.cget("text"), font=self.cget("font"))
        temp.pack()
        height = temp.winfo_reqheight()
        temp.destroy()

        # Update scanline position with smooth reversing
        self.scanline_pos += self.scan_speed * self.scan_direction
        if self.scanline_pos >= height or self.scanline_pos <= 0:
            self.scan_direction *= -1  # Reverse direction at edges

        # Create advanced scanline effect
        if 0 <= self.scanline_pos <= height:
            # Calculate distance from scanline for gradient effect
            def get_color_at_position(y_pos):
                distance = abs(self.scanline_pos - y_pos)
                max_distance = 10  # Width of the glow effect
                if distance > max_distance:
                    return "#FF7B00"  # Base orange color
                
                # Calculate brightness boost based on distance
                intensity = 1 - (distance / max_distance)
                brightness = int(90 * intensity)  # Increased brightness boost
                r, g, b = int(0xFF), int(0x7B), int(0x00)  # Base orange color
                r = min(255, r + brightness)
                g = min(255, g + brightness)
                b = min(255, b + brightness)
                return f"#{r:02x}{g:02x}{b:02x}"
            
            # Apply gradient effect
            current_color = get_color_at_position(height/2)
            self.configure(fg=current_color)
        else:
            self.configure(fg="#FF7B00")  # Base orange color

        # Create interlacing effect
        if int(self.scanline_pos) % 4 < 2:  # Interlacing pattern
            brightness = 20
            r, g, b = int(0xFF), int(0x7B), int(0x00)
            r = min(255, r + brightness)
            g = min(255, g + brightness)
            b = min(255, b + brightness)
            self.configure(fg=f"#{r:02x}{g:02x}{b:02x}")
        
        # Schedule next animation frame
        self.after(20, self.animate_scanline)  # Faster update rate for smoother animation
