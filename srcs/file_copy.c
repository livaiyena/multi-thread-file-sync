#include "sync.h"

static long	do_copy_loop(int fd_src, int fd_dst)
{
	char	buf[BLOCK_SIZE];
	ssize_t	bytes_read;
	long	total;

	total = 0;
	bytes_read = read(fd_src, buf, BLOCK_SIZE);
	while (bytes_read > 0)
	{
		if (write(fd_dst, buf, bytes_read) != bytes_read)
		{
			perror("write");
			return (-1);
		}
		total += bytes_read;
		bytes_read = read(fd_src, buf, BLOCK_SIZE);
	}
	if (bytes_read < 0)
	{
		perror("read");
		return (-1);
	}
	return (total);
}

int	copy_file_blocks(const char *src, const char *dst)
{
	int		fds[2];
	long	total;

	if (open_src_dst(src, dst, fds) == -1)
		return (-1);
	total = do_copy_loop(fds[0], fds[1]);
	close(fds[0]);
	close(fds[1]);
	return (total);
}

int	ensure_parent_dir(const char *path)
{
	char	parent[MAX_PATH_LEN];
	char	*last_slash;

	strncpy(parent, path, MAX_PATH_LEN - 1);
	parent[MAX_PATH_LEN - 1] = '\0';
	last_slash = strrchr(parent, '/');
	if (!last_slash)
		return (0);
	*last_slash = '\0';
	return (mkdir_recursive(parent));
}
