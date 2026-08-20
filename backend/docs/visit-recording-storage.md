# Visit recording storage

Visit recordings use a provider-neutral private object key. Local filesystem
storage is the default for development; S3-compatible storage supports
DigitalOcean Spaces. Playback always streams through the authenticated backend,
so buckets and objects must not be public.

## Local development

Set `VISIT_RECORDING_STORAGE_PROVIDER=local`. The default storage directory is
`backend/storage/visit_recordings`; override it with
`VISIT_RECORDING_STORAGE_DIR`. The directory is local runtime data and must not
be committed.

## DigitalOcean Spaces

Create a private Space and provide these environment variables to the backend:

```dotenv
VISIT_RECORDING_STORAGE_PROVIDER=s3
VISIT_RECORDING_S3_ENDPOINT=https://nyc3.digitaloceanspaces.com
VISIT_RECORDING_S3_REGION=nyc3
VISIT_RECORDING_S3_BUCKET=your-private-space
VISIT_RECORDING_S3_ACCESS_KEY=
VISIT_RECORDING_S3_SECRET_KEY=
VISIT_RECORDING_MAX_UPLOAD_BYTES=262144000
```

Use runtime secrets for credentials. Do not place credentials in source,
images, logs, or committed environment files. Objects are uploaded without a
public ACL.

## Validation and retention

Accepted MIME types are WebM, Ogg, MP3, WAV, and M4A audio. The byte limit is
enforced while the provider reads the upload. Object keys contain only
server-generated tenant, patient, and recording UUIDs.

The delete API is a retention-preserving soft delete: it hides the database
record while retaining the private object. Missing objects produce an explicit
404 during playback. If a database write fails after upload, the backend removes
the object; a cleanup failure is surfaced for operator attention. A future
policy-driven purge job should delete the object first, treat an already-missing
object as idempotent success, and only then remove or tombstone the database
record. No automatic retention period is currently configured.

Transcript fields remain provider-neutral. Azure Speech storage or
transcription is not configured by this change.
