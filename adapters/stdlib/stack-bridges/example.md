# an example stack with bridges: nine steps, six of them taking what an earlier one made

Read it with:

    python adapters/stdlib/stack-bridges/stack_bridges.py --stack adapters/stdlib/stack-bridges/example.md

It is for reading, not running: `<pile>` and `<scratch>` stand for your
folder and a folder a stack may write to.

## read once, then asked
- code-comments -- mirror --from <pile> --to {box}-code
- index-cache -- --from {box}-code --to <scratch>/kept/index
- scan -- scan --index <scratch>/kept/index --questions <scratch>/questions.txt
- glance -- --of {03} --questions <scratch>/questions.txt

## kept, and checked
- backup -- --box {box} --to <scratch>/usb
- restore-drill -- --from <scratch>/usb/willow-backup.zip
- three-two-one -- --box {box} --copy usb:<scratch>/usb/willow-backup.zip
- fixity -- --box {box}
- history -- --box {box}
