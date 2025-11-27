#!/bin/bash
# Install Java 11 (required for Spark, Hive, Impala)

echo "Installing Java 11 JDK..."
echo ""
echo "This requires sudo password. Please run:"
echo ""
echo "  sudo apt update"
echo "  sudo apt install -y openjdk-11-jdk"
echo ""
echo "After installation, verify with:"
echo "  java -version"
echo ""
echo "Then run ./start-demo.sh"