# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2020 - nimar3
"""

import enum


class RequestStatus(enum.Enum):
    QUEUED = 1
    COMPILING = 2
    DEPLOYING = 3
    WAITING = 4
    RUNNING = 5
    FINISHED = 6
    CANCELED = 7
    ERROR = 9
    TIMEWALL = 10

    @property
    def label(self):
        """
        Dictionary to map enum to Bootstrap labels
        """
        label_dict = {RequestStatus.QUEUED: 'label-default', RequestStatus.COMPILING: 'label-info',
                      RequestStatus.DEPLOYING: 'label-info', RequestStatus.WAITING: 'label-info',
                      RequestStatus.RUNNING: 'label-primary', RequestStatus.FINISHED: 'label-success',
                      RequestStatus.CANCELED: 'label-warning', RequestStatus.ERROR: 'label-danger',
                      RequestStatus.TIMEWALL: 'label-warning'}
        return label_dict[self] if self in label_dict else 'label-default'
