import os
import subprocess
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import logging

class JobScheduler:
    def __init__(self, interval_seconds=5):
        self.interval_seconds = interval_seconds
        self.scheduler = BlockingScheduler(daemon=True)
        self.setup_logging()
        
    def setup_logging(self):
        """Configure logging for the scheduler"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scheduler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('JobScheduler')

    def run_job(self):
        """Execute the main job"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.logger.info(f"Job started at {current_date}")

            script_path = os.path.join(
                os.path.split(os.path.abspath(__file__))[0], 
                "main.py"
            )
            
            result = subprocess.run(
                ["python", script_path],
                shell=True,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.logger.info("Job completed successfully")
                if result.stdout:
                    self.logger.debug(f"Output: {result.stdout}")
            else:
                self.logger.error(f"Job failed with error: {result.stderr}")

        except Exception as e:
            self.logger.error(f"Error executing job: {str(e)}")
            raise

    def on_job_executed(self, event):
        """Handle successful job execution"""
        if event.exception:
            self.logger.error(f'Job failed: {event.exception}')
        else:
            self.logger.info('Job executed successfully')

    def start(self):
        """Start the scheduler"""
        try:
            self.logger.info(f"Starting scheduler with {self.interval_seconds} second interval")
            
            # Add the job
            self.scheduler.add_job(
                self.run_job, 
                'interval', 
                seconds=self.interval_seconds,
                id='main_job'
            )

            # Add listeners for job events
            self.scheduler.add_listener(
                self.on_job_executed, 
                EVENT_JOB_ERROR | EVENT_JOB_EXECUTED
            )

            # Start the scheduler
            self.scheduler.start()

        except (KeyboardInterrupt, SystemExit):
            self.logger.info("Scheduler shutdown requested")
            self.stop()
        except Exception as e:
            self.logger.error(f"Error in scheduler: {str(e)}")
            self.stop()

    def stop(self):
        """Stop the scheduler"""
        try:
            self.scheduler.shutdown()
            self.logger.info("Scheduler stopped")
        except Exception as e:
            self.logger.error(f"Error stopping scheduler: {str(e)}")

if __name__ == "__main__":
    # Create and start the scheduler
    scheduler = JobScheduler(interval_seconds=5)
    scheduler.start()