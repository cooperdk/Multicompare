# Use a recent Ubuntu image for stability
FROM ubuntu:22.04

# Set environment variables for non-interactive installs
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies:
# 1. Python, pip, git
# 2. build-essential (gcc/g++) for C compilation
# 3. Nuitka requirements (patchelf for binary patching)
# 4. rawpy dependencies (libraw-dev, libjpeg-dev, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    git \
    build-essential \
    patchelf \
    libjpeg-dev \
    zlib1g-dev \
    libtiff-dev \
    libraw-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python packages globally
RUN python3 -m pip install --upgrade pip setuptools wheel
RUN python3 -m pip install nuitka

# Set up the working directory inside the container
WORKDIR /app

# Copy the entire project code into the container
COPY . /app

# Install project dependencies (Pillow, rawpy, etc.)
# We install the editable version of the project so Nuitka can find all source files.
RUN python3 -m pip install -r requirements.txt && \
    python3 -m pip install -e .

# The default command when the container runs is to execute the build script
CMD ["python3", "scripts/build.py"]