import quixstreams as qx
from quix_function import QuixFunction
from transformers import pipeline
import os

classifier = pipeline('sentiment-analysis')

# Quix injects credentials automatically to the client.
# Alternatively, you can always pass an SDK token manually as an argument.
client = qx.QuixStreamingClient('sdk-905f0c6001434d0e8e03f26c1a4b34e2')

# Change consumer group to a different constant if you want to run model locally.
print("Opening input and output topics")

consumer_topic = client.get_topic_consumer(
    'messages',
    "sentiment-analysis3",
    auto_offset_reset = qx.AutoOffsetReset.Earliest)

producer_topic = client.get_topic_producer('sentiment')
producer_topic_sanitized = client.get_topic_producer('messages_sanitized')

# Callback called for each incoming stream
def read_stream(consumer_stream: qx.StreamConsumer):

    # Create a new stream to output data
    producer_stream = producer_topic.get_or_create_stream(consumer_stream.stream_id)
    producer_stream.properties.parents.append(consumer_stream.stream_id)

    producer_sanitized_stream = producer_topic_sanitized.get_or_create_stream(consumer_stream.stream_id)
    producer_sanitized_stream.properties.parents.append(consumer_stream.stream_id)
    # handle the data in a function to simplify the example
    quix_function = QuixFunction(consumer_stream, producer_stream, producer_sanitized_stream, classifier)

    buffer = consumer_stream.timeseries.create_buffer()
    buffer.time_span_in_milliseconds = 200
    buffer.buffer_timeout = 200

    # React to new data received from input topic.
    buffer.on_dataframe_released = quix_function.on_dataframe_handler

    # When input stream closes, we close output stream as well. 
    def on_stream_close(stream_consumer: qx.StreamConsumer, end_type: qx.StreamEndType):
        producer_stream.close()
        print("Stream closed:" + producer_stream.stream_id)

    consumer_stream.on_stream_closed = on_stream_close


# Subscribe to events before initiating read to avoid losing out on any data
consumer_topic.on_stream_received = read_stream

print("Listening to streams. Press CTRL-C to exit.")

# Handle graceful exit of the model.
qx.App.run()