```bash
aws cloudformation create-stack \
  --stack-name nextflow-batch \
  --template-body file://infrastructure/aws_nextflow_batch.yaml \
  --capabilities CAPABILITY_NAMED_IAM
```
