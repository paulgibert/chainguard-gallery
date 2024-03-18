deps:
	gcloud components install pubsub-emulator
	gcloud components update
topic:
	gcloud pubsub topics create to-scan

