FROM odoo:18.0

USER root

# Install Python dependencies required by face_attendance
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3-grpcio \
        python3-protobuf \
    && rm -rf /var/lib/apt/lists/*

USER odoo
