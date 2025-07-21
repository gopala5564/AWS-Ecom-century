FROM public.ecr.aws/lambda/python:3.9

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install dependencies
RUN pip install -r requirements.txt

# Copy function code
COPY lambda/etl_processor.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD [ "etl_processor.handler" ]
