#!/usr/bin/env python3
from textwrap import dedent

from caproto.server import PVGroup, ioc_arg_parser, pvproperty, run


class MonoIOC(PVGroup):
    """
    An IOC with three uncoupled read/writable PVs.

    """

    theta = pvproperty(value=0.0, doc="A float")
    two_theta = pvproperty(value=0.0, doc="A float")


if __name__ == "__main__":
    ioc_options, run_options = ioc_arg_parser(
        default_prefix="mono:", desc=dedent(MonoIOC.__doc__)
    )
    ioc = MonoIOC(**ioc_options)
    run(ioc.pvdb, **run_options)
