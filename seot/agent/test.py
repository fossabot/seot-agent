import asyncio
import logging

from .dataflow import DAG
from .sinks import DebugSink
from .sources import ConstSource
from .transformers import IdentityTransformer

if __name__ == "__main__":
    sink = DebugSink(name="debug")
    source = ConstSource(123, 1, name="foo")
    source2 = ConstSource("hogeppi", 2, name="hoge")
    transformer = IdentityTransformer(name="identity")
    source.connect(transformer).connect(sink)
    source2.connect(transformer)

    loop = asyncio.get_event_loop()

    dag = DAG(source, source2)
    try:
        dag.run()
    except KeyboardInterrupt:
        dag.stop()

    loop.close()
