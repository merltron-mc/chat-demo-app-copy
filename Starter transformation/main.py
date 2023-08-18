import quixstreams as qx
import os
from tqdm import tqdm

client = qx.QuixStreamingClient()

topic_consumer = client.get_topic_consumer(os.environ["input"], consumer_group = "counter", auto_offset_reset=qx.AutoOffsetReset.Latest)
topic_producer = client.get_topic_producer(os.environ["output"])


def on_data_released(stream_consumer: qx.StreamConsumer, data: qx.TimeseriesData):
    stream_producer = topic_producer.get_or_create_stream(stream_id = "count")
    stream_producer.timeseries.buffer.add_timestamp_nanoseconds(data.timestamps[0].timestamp_nanoseconds) \
        .add_value("count", len(data.timestamps)) \
        .publish()
    bar.update()
    print(str(data.timestamps[0].timestamp_milliseconds) + " - " + str(data.timestamps[-1].timestamp_milliseconds) + " count: " + str(len(data.timestamps)))



def on_stream_received_handler(stream_consumer: qx.StreamConsumer):
    buffer = stream_consumer.timeseries.create_buffer()
    buffer.on_data_released = on_data_released


# subscribe to new streams being received
topic_consumer.on_stream_received = on_stream_received_handler


bar = tqdm(desc="Receiving messages")

# Handle termination signals and provide a graceful exit
qx.App.run()