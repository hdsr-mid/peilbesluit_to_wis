def get_progress(iteration_nr: int, nr_to_do: int):
    progress_percentage = int((100 * iteration_nr) / nr_to_do)
    return progress_percentage
