import cv2
import numpy as np
import mediapipe as mp
import time

# MediaPipe setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

canvas = None
prev_x, prev_y = 0, 0

# Colors
colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 0, 255)]
color_index = 0
draw_color = colors[color_index]

last_clear_time = 0

while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)

    if canvas is None:
        canvas = np.zeros_like(frame)

    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        for hand in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

            # Finger landmarks
            ix, iy = int(hand.landmark[8].x * w), int(hand.landmark[8].y * h)
            mx = hand.landmark[12].y < hand.landmark[10].y
            rx = hand.landmark[16].y < hand.landmark[14].y
            px = hand.landmark[20].y < hand.landmark[18].y
            index_up = hand.landmark[8].y < hand.landmark[6].y
            middle_up = mx
            ring_up = rx
            pinky_up = px
            thumb_up = hand.landmark[4].x < hand.landmark[3].x

            fingers_up = [thumb_up, index_up, middle_up, ring_up, pinky_up]

            # Draw point
            cv2.circle(frame, (ix, iy), 8, (0, 255, 0), -1)

            # ✋ CLEAR CANVAS (all fingers up)
            if all(fingers_up):
                current_time = time.time()
                if current_time - last_clear_time > 1:
                    canvas = np.zeros_like(frame)
                    prev_x, prev_y = 0, 0
                    last_clear_time = current_time

            # ✌ CHANGE COLOR
            elif index_up and middle_up:
                color_index = (color_index + 1) % len(colors)
                draw_color = colors[color_index]
                prev_x, prev_y = 0, 0
                cv2.waitKey(300)

            # 👆 DRAW
            elif index_up:
                if prev_x == 0 and prev_y == 0:
                    prev_x, prev_y = ix, iy
                cv2.line(canvas, (prev_x, prev_y), (ix, iy), draw_color, 6)
                prev_x, prev_y = ix, iy
            else:
                prev_x, prev_y = 0, 0

    else:
        prev_x, prev_y = 0, 0

    # Merge canvas and frame
    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    _, inv = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY_INV)
    inv = cv2.cvtColor(inv, cv2.COLOR_GRAY2BGR)
    frame = cv2.bitwise_and(frame, inv)
    frame = cv2.bitwise_or(frame, canvas)

    # ---------------- UI HEADING ----------------
    cv2.rectangle(frame, (0, 0), (w, 50), (0, 0, 0), -1)  # black background
    cv2.putText(frame, "Air Canvas", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)  # yellow text

    # ---------------- UI ACTIONS ----------------
    cv2.putText(frame, "S: Save | Q: Quit | Palm: Clear",
                (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)  # black text

    # ---------------- COLOR INDICATOR ----------------
    cv2.rectangle(frame, (10, 90), (60, 140), draw_color, -1)

    cv2.imshow("Air Canvas PRO", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('c'):
        canvas = np.zeros_like(frame)
        prev_x, prev_y = 0, 0
    elif key == ord('s'):
        cv2.imwrite("air_canvas_drawing.png", canvas)
        print("✅ Drawing saved as air_canvas_drawing.png")

cap.release()
cv2.destroyAllWindows()
