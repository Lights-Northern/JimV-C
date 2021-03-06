#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = 'James Iter'
__date__ = '2018/9/30'
__contact__ = 'james.iter.cn@gmail.com'
__copyright__ = '(c) 2018 by James Iter.'


import traceback
import signal
import time
import os
import threading

from jimvc.models import app_config, logger
from jimvc.models import EventProcessor, Init
from jimvc.models import Utils
from jimvc import app
from jimvc import ws_engine_for_vnc


threads = []
# noinspection PyBroadException
try:
    signal.signal(signal.SIGTERM, Utils.signal_handle)
    signal.signal(signal.SIGINT, Utils.signal_handle)

    pid = os.fork()
    if pid == 0:
        ws_engine_for_vnc()

    else:
        # 父进程退出时，会清理所有提前退出的子进程的环境。所以这里无需对子进程做等待操作。
        # 即：即使子进程提前退出，且因父进程没有做wait处理，使其变成了僵尸进程。但当父进程退出时，会对因其所产生的僵尸进程做统一清理操作。

        t_ = threading.Thread(target=EventProcessor.launch, args=())
        threads.append(t_)

        t_ = threading.Thread(target=Init.pub_sub_ping_pong, args=())
        threads.append(t_)

        t_ = threading.Thread(target=Init.clear_expire_monitor_log, args=())
        threads.append(t_)

        for t in threads:
            t.start()

except:
    logger.error(traceback.format_exc())
    exit(-1)


if __name__ == '__main__':
    # noinspection PyBroadException
    try:

        app.run(host=app_config['listen'], port=app_config['port'], use_reloader=False, threaded=True)

        while True:
            if Utils.exit_flag:
                # 主线程即将结束
                break
            time.sleep(1)

        # 等待子线程结束
        for t in threads:
            t.join()

        print 'Main say bye-bye!'

    except:
        logger.error(traceback.format_exc())
        exit(-1)

