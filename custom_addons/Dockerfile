FROM odoo:17.0

USER root

# Install Python dependencies
COPY attendance_system/requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

USER odoo
