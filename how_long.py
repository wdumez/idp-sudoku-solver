"""Calculate how long it would take for the ZebraTutor method to complete."""


def main() -> None:
    """Main."""
    nr_given = 36
    nr_cells = 9*9
    nr_threads = 2
    max_steps = 0  # use 0 for all steps
    avg_core_time_sec = 5*60

    print('Nr. of givens:')
    print(nr_given)
    print('Nr. of cells:')
    print(nr_cells)
    print('Maximum number of steps to calculate:')
    print(max_steps)
    print('-'*20)

    # sum(N-i); for i = n through i = N - 1
    num_cores = 0
    for step, i in enumerate(range(nr_given, nr_cells), start=1):
        if step > max_steps and max_steps != 0:
            break
        num_cores += nr_cells - i

    print("Total number of cores to calculate:")
    print(f"{num_cores}")

    seconds = avg_core_time_sec * num_cores
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    print("Total time to calculate all cores sequentially:")
    print(f"{hours}h {minutes}m {seconds}s")

    seconds = avg_core_time_sec * num_cores
    seconds /= nr_threads
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    print(f"If multithreading with {nr_threads} threads:")
    print(f"{hours}h {minutes}m {seconds}s")


if __name__ == '__main__':
    main()
