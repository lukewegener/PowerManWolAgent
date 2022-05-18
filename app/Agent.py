from datetime import datetime, timedelta
import json, os
from azure.storage.queue import QueueClient
from azure.identity import DefaultAzureCredential
from wakeonlan import send_magic_packet
from loguru import logger

class Agent:
    def __init__(self, agent_config, queue_client):
        self.agent_config = agent_config
        self.queue_client = queue_client

    def get_messages(self):
        messages = []
        for message in self.queue_client.receive_messages():
            messages.append(message)
        logger.info(f'Found {len(messages)} messages')
        return messages

    def process_messages(self, messages):
        for message in messages:
            job = Job(json.loads(message.content))
            job.process()
            self.queue_client.delete_message(message)

class Job:
    def __init__(self, job_config):
        self.job_config = job_config

    def process(self):
        logger.info(f'Processing job: {self.job_config}')
        match self.job_config['type'].lower(): 
            case 'wol':
                mac = self.job_config['mac'].replace(':', '').replace('-', '').replace('.', '').lower()
                send_magic_packet(mac)
                logger.info(f'WOL packet sent to {mac}')
            case _:
                logger.error(f'Unknown job type: {self.job_config["type"]}')
            
def main():
    initial_agent_config = {
        "poll_interval": int(os.environ['POLL_INTERVAL']),
        "storage_account_name": os.environ['STORAGE_ACCOUNT_NAME'],
        "queue_name": os.environ['QUEUE_NAME']
    }
    
    logger.info(f'Initializing agent with config: {initial_agent_config}')

    credential = DefaultAzureCredential()
    queue_client = QueueClient.from_queue_url(queue_url="https://{}.queue.core.windows.net/{}".format(initial_agent_config['storage_account_name'], initial_agent_config['queue_name']), credential=credential)
    agent = Agent(initial_agent_config, queue_client)

    last = datetime.now()
    while True:
        if datetime.now() - last > timedelta(seconds = initial_agent_config['poll_interval']):
            last = datetime.now()
            try:
                messages = agent.get_messages()
                agent.process_messages(messages)
            except Exception as e:
                logger.error(e)

if __name__ == "__main__":
    main()
