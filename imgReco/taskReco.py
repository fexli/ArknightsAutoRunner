def recognizeTaskLeft(ark, replace=None):
    TaskL = ['UNRECO', 'UNRECO', 'UNRECO', 'UNRECO', 'UNRECO', 'UNRECO']
    TaskI = {'main\\task\\task_fin.png': 'FINISH',
             'main\\task\\task_3.png': 'TASK3_0',
             'main\\task\\task_3_t1.png': 'TASK3_1',
             'main\\task\\task_3_t2.png': 'TASK3_2',
             'main\\task\\task_2.png': 'TASK2_0',
             'main\\task\\task_2_t1.png': 'TASK2_1',
             'main\\task\\task_1.png': 'TASK1_0'}
    for k, v in TaskI.items():
        for x, y in ark.gameTemp.dingwei(k, ark.getScreenShot(39, 147, 138, 490), 0.9):
            TaskL[int((y - 3) / 89)] = v
    return TaskL
