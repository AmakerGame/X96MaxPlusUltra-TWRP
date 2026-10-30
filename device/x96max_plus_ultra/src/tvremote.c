#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

static int sync_clock_from_rtc(void) {
    char value[64];
    int fd = open("/sys/class/rtc/rtc0/since_epoch", O_RDONLY);
    if (fd < 0) return -1;
    ssize_t n = read(fd, value, sizeof(value) - 1);
    close(fd);
    if (n <= 0) return -1;
    value[n] = '\0';
    char *end = NULL;
    long long epoch = strtoll(value, &end, 10);
    if (end == value || epoch < 1609459200LL) return -1;
    struct timespec current;
    if (clock_gettime(CLOCK_REALTIME, &current) < 0) return -1;
    if (llabs((long long)current.tv_sec - epoch) > 2) {
        struct timespec corrected = {(time_t)epoch, 0};
        if (clock_settime(CLOCK_REALTIME, &corrected) < 0) return -1;
    }
    return 0;
}

int main(void) {
    return sync_clock_from_rtc() == 0 ? 0 : 1;
}
