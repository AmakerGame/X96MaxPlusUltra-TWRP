/* Convert remote D-pad key events into virtual mouse movement for TWRP. */
#include <errno.h>
#include <fcntl.h>
#include <linux/input.h>
#include <linux/uinput.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <time.h>
#include <unistd.h>

#define MAX_INPUTS 64
#define STEP 36

static int mouse_fd = -1;

static void send_event(unsigned short type, unsigned short code, int value) {
    struct input_event ev;
    memset(&ev, 0, sizeof(ev));
    ev.type = type;
    ev.code = code;
    ev.value = value;
    if (write(mouse_fd, &ev, sizeof(ev)) != (ssize_t)sizeof(ev))
        perror("tvremote: uinput write");
}

static void sync_event(void) {
    send_event(EV_SYN, SYN_REPORT, 0);
}

static void click_left(void) {
    send_event(EV_KEY, BTN_LEFT, 1);
    sync_event();
    /* Keep the press visible to recovery's slower GUI input loop. */
    usleep(300000);
    send_event(EV_KEY, BTN_LEFT, 0);
    sync_event();
}

static void send_key(unsigned short code) {
    send_event(EV_KEY, code, 1);
    sync_event();
    send_event(EV_KEY, code, 0);
    sync_event();
}

static void handle_key(unsigned short code, int value) {
    int dx = 0, dy = 0;
    if (value == 0) return;
    switch (code) {
        case KEY_UP:    dy = -STEP; break;
        case KEY_DOWN:  dy = STEP; break;
        case KEY_LEFT:  dx = -STEP; break;
        case KEY_RIGHT: dx = STEP; break;
        case KEY_ENTER:
        case KEY_KPENTER:
        case KEY_OK:
        case BTN_SOUTH:
            if (value == 1) click_left();
            return;
        case KEY_BACK:
        case KEY_ESC:
            if (value == 1) send_key(KEY_ESC);
            return;
        case KEY_HOME:
            if (value == 1) send_key(KEY_HOME);
            return;
        default:
            return;
    }
    send_event(EV_REL, REL_X, dx);
    send_event(EV_REL, REL_Y, dy);
    sync_event();
}

static int has_bit(const unsigned long *bits, int bit) {
    return (bits[bit / (8 * sizeof(unsigned long))] >>
            (bit % (8 * sizeof(unsigned long))) & 1UL) != 0;
}

static int is_remote(int fd) {
    unsigned long evbits[(EV_MAX + 8 * sizeof(unsigned long)) /
                         (8 * sizeof(unsigned long))];
    unsigned long keybits[(KEY_MAX + 8 * sizeof(unsigned long)) /
                          (8 * sizeof(unsigned long))];
    unsigned long relbits[(REL_MAX + 8 * sizeof(unsigned long)) /
                          (8 * sizeof(unsigned long))];
    memset(evbits, 0, sizeof(evbits));
    memset(keybits, 0, sizeof(keybits));
    memset(relbits, 0, sizeof(relbits));
    if (ioctl(fd, EVIOCGBIT(0, sizeof(evbits)), evbits) < 0 ||
        !has_bit(evbits, EV_KEY)) return 0;
    if (ioctl(fd, EVIOCGBIT(EV_KEY, sizeof(keybits)), keybits) < 0) return 0;
    /* The IR keypad already emits native REL_X/REL_Y mouse motion. Its OK
       key is mapped to BTN_LEFT in the device's remote table; don't double
       move its cursor here. This helper is for keyboard-only USB remotes. */
    if (has_bit(evbits, EV_REL) &&
        ioctl(fd, EVIOCGBIT(EV_REL, sizeof(relbits)), relbits) == 0 &&
        has_bit(relbits, REL_X) && has_bit(relbits, REL_Y)) return 0;
    return (has_bit(keybits, KEY_UP) || has_bit(keybits, KEY_DOWN) ||
            has_bit(keybits, KEY_LEFT) || has_bit(keybits, KEY_RIGHT)) &&
           (has_bit(keybits, KEY_ENTER) || has_bit(keybits, KEY_KPENTER) ||
            has_bit(keybits, KEY_OK) || has_bit(keybits, BTN_SOUTH));
}

static int create_virtual_mouse(void) {
    struct uinput_user_dev dev;
    mouse_fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    if (mouse_fd < 0) {
        perror("tvremote: open /dev/uinput");
        return -1;
    }
    if (ioctl(mouse_fd, UI_SET_EVBIT, EV_REL) < 0 ||
        ioctl(mouse_fd, UI_SET_RELBIT, REL_X) < 0 ||
        ioctl(mouse_fd, UI_SET_RELBIT, REL_Y) < 0 ||
        ioctl(mouse_fd, UI_SET_EVBIT, EV_KEY) < 0 ||
        ioctl(mouse_fd, UI_SET_KEYBIT, BTN_LEFT) < 0 ||
        ioctl(mouse_fd, UI_SET_KEYBIT, KEY_ESC) < 0 ||
        ioctl(mouse_fd, UI_SET_KEYBIT, KEY_HOME) < 0) {
        perror("tvremote: configure uinput");
        close(mouse_fd);
        mouse_fd = -1;
        return -1;
    }
    memset(&dev, 0, sizeof(dev));
    snprintf(dev.name, UINPUT_MAX_NAME_SIZE, "X96 TV Remote Pointer");
    dev.id.bustype = BUS_VIRTUAL;
    dev.id.vendor = 0x096e;
    dev.id.product = 0x0096;
    dev.id.version = 1;
    if (write(mouse_fd, &dev, sizeof(dev)) != (ssize_t)sizeof(dev) ||
        ioctl(mouse_fd, UI_DEV_CREATE) < 0) {
        perror("tvremote: create virtual input device");
        close(mouse_fd);
        mouse_fd = -1;
        return -1;
    }
    return 0;
}

static int sync_clock_from_rtc(void) {
    char value[64];
    int fd = open("/sys/class/rtc/rtc0/since_epoch", O_RDONLY);
    if (fd < 0) {
        perror("tvremote: open RTC epoch");
        return -1;
    }
    ssize_t n = read(fd, value, sizeof(value) - 1);
    close(fd);
    if (n <= 0) return -1;
    value[n] = '\0';
    char *end = NULL;
    long long epoch = strtoll(value, &end, 10);
    if (end == value || epoch < 1609459200LL) {
        fprintf(stderr, "tvremote: invalid RTC epoch: %s\n", value);
        return -1;
    }
    struct timespec current;
    if (clock_gettime(CLOCK_REALTIME, &current) < 0) return -1;
    if (llabs((long long)current.tv_sec - epoch) > 2) {
        struct timespec corrected = {(time_t)epoch, 0};
        if (clock_settime(CLOCK_REALTIME, &corrected) < 0) {
            perror("tvremote: set system clock from RTC");
            return -1;
        }
        fprintf(stderr, "tvremote: system clock set from RTC (%lld)\n", epoch);
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--set-time") == 0)
        return sync_clock_from_rtc() == 0 ? 0 : 1;
    sync_clock_from_rtc();
    struct pollfd pfds[MAX_INPUTS];
    int count = 0;
    if (create_virtual_mouse() < 0) return 1;

    /* Input devices are normally ready before init starts recovery services. */
    for (int attempt = 0; attempt < 10 && count == 0; ++attempt) {
        char path[64];
        for (int i = 0; i < MAX_INPUTS; ++i) {
            snprintf(path, sizeof(path), "/dev/input/event%d", i);
            int fd = open(path, O_RDONLY | O_NONBLOCK);
            if (fd < 0) continue;
            if (is_remote(fd)) {
                pfds[count].fd = fd;
                pfds[count].events = POLLIN;
                pfds[count].revents = 0;
                ++count;
                fprintf(stderr, "tvremote: listening on %s\n", path);
            } else {
                close(fd);
            }
        }
        if (count == 0) sleep(1);
    }
    if (count == 0) {
        fprintf(stderr, "tvremote: no D-pad input devices found\n");
        ioctl(mouse_fd, UI_DEV_DESTROY);
        close(mouse_fd);
        return 2;
    }

    for (;;) {
        int ready = poll(pfds, (nfds_t)count, -1);
        if (ready < 0) {
            if (errno == EINTR) continue;
            perror("tvremote: poll");
            break;
        }
        for (int i = 0; i < count; ++i) {
            if (!(pfds[i].revents & POLLIN)) continue;
            struct input_event ev;
            ssize_t n = read(pfds[i].fd, &ev, sizeof(ev));
            if (n == (ssize_t)sizeof(ev) && ev.type == EV_KEY)
                handle_key(ev.code, ev.value);
        }
    }
    for (int i = 0; i < count; ++i) close(pfds[i].fd);
    ioctl(mouse_fd, UI_DEV_DESTROY);
    close(mouse_fd);
    return 0;
}
