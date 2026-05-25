NAME      = filesync
CC        = cc
CFLAGS    = -Wall -Wextra -Werror -pthread
INCLUDES  = -I includes

SRCS_DIR  = srcs
SRCS      = $(SRCS_DIR)/main.c \
            $(SRCS_DIR)/scanner.c \
            $(SRCS_DIR)/scanner_utils.c \
            $(SRCS_DIR)/task_queue.c \
            $(SRCS_DIR)/thread_pool.c \
            $(SRCS_DIR)/file_copy.c \
            $(SRCS_DIR)/file_copy_utils.c \
            $(SRCS_DIR)/logger.c \
            $(SRCS_DIR)/perf.c \
            $(SRCS_DIR)/logger_utils.c \
            $(SRCS_DIR)/error.c
OBJS      = $(SRCS:.c=.o)

all:        $(NAME)

$(NAME):    $(OBJS)
	$(CC) $(CFLAGS) $(OBJS) -o $(NAME)

%.o:        %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

clean:
	rm -f $(OBJS) \
    rm -rf tests/__pycache__/

fclean:     clean
	rm -f $(NAME) \
    rm -rf tests/__pycache__/

re:         fclean all

test:       $(NAME)
	@bash run_test.sh

pytest:     $(NAME)
	@cd tests && python3 run_tests.py

benchmark:  $(NAME)
	@bash benchmark.sh

.PHONY:     all clean fclean re test pytest benchmark
