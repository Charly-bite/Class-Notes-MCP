#!/usr/bin/env python3
"""
Audio System Test Script
Tests basic audio recording capabilities on Parrot OS
"""

import pyaudio
import sys
import time

def test_audio_system():
    """Test if PyAudio can access audio devices"""
    print("🎵 Testing Audio System...")
    print("=" * 50)
    
    try:
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        print(f"PyAudio Version: {pyaudio.__version__}")
        print(f"Available Audio Devices: {p.get_device_count()}")
        print()
        
        # List all audio devices
        print("📱 Available Audio Devices:")
        print("-" * 30)
        
        input_devices = []
        output_devices = []
        
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            device_name = device_info['name']
            max_input_channels = device_info['maxInputChannels']
            max_output_channels = device_info['maxOutputChannels']
            
            print(f"Device {i}: {device_name}")
            print(f"  Input Channels: {max_input_channels}")
            print(f"  Output Channels: {max_output_channels}")
            print(f"  Sample Rate: {device_info['defaultSampleRate']}")
            
            if max_input_channels > 0:
                input_devices.append((i, device_name))
            if max_output_channels > 0:
                output_devices.append((i, device_name))
            print()
        
        # Show default devices
        try:
            default_input = p.get_default_input_device_info()
            default_output = p.get_default_output_device_info()
            
            print("🎤 Default Input Device:")
            print(f"  {default_input['name']} (Index: {default_input['index']})")
            print()
            
            print("🔊 Default Output Device:")
            print(f"  {default_output['name']} (Index: {default_output['index']})")
            print()
            
        except Exception as e:
            print(f"⚠️ Warning: Could not get default devices: {e}")
        
        # Test basic recording capability
        print("🎯 Testing Recording Capability...")
        print("-" * 30)
        
        if input_devices:
            try:
                # Try to open an input stream
                test_device_index = input_devices[0][0]
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=44100,
                    input=True,
                    input_device_index=test_device_index,
                    frames_per_buffer=1024
                )
                
                print(f"✅ Successfully opened input stream on: {input_devices[0][1]}")
                stream.close()
                
            except Exception as e:
                print(f"❌ Failed to open input stream: {e}")
        else:
            print("❌ No input devices found!")
        
        p.terminate()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 SUMMARY:")
        print(f"  Input devices found: {len(input_devices)}")
        print(f"  Output devices found: {len(output_devices)}")
        
        if len(input_devices) > 0:
            print("\n🎤 Recommended for Recording:")
            for idx, name in input_devices[:3]:  # Show top 3
                print(f"  Device {idx}: {name}")
        
        return len(input_devices) > 0
        
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure pulseaudio is running: systemctl --user start pulseaudio")
        print("2. Check audio permissions: sudo usermod -a -G audio $USER")
        print("3. Restart your session after adding to audio group")
        return False

def test_basic_recording():
    """Test a 3-second recording"""
    print("\n🎙️ Testing 3-Second Recording...")
    print("Speak into your microphone for 3 seconds...")
    
    try:
        p = pyaudio.PyAudio()
        
        # Recording parameters
        chunk = 1024
        format = pyaudio.paInt16
        channels = 1
        rate = 44100
        record_seconds = 3
        
        # Open stream
        stream = p.open(
            format=format,
            channels=channels,
            rate=rate,
            input=True,
            frames_per_buffer=chunk
        )
        
        print("🔴 Recording... (3 seconds)")
        frames = []
        
        for i in range(0, int(rate / chunk * record_seconds)):
            data = stream.read(chunk)
            frames.append(data)
            
            # Simple progress indicator
            progress = (i + 1) / (rate / chunk * record_seconds)
            bars = int(progress * 20)
            print(f"\r[{'='*bars}{' '*(20-bars)}] {progress:.0%}", end='', flush=True)
        
        print("\n✅ Recording completed!")
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        return True
        
    except Exception as e:
        print(f"❌ Recording failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Cybersecurity Audio MCP - System Test")
    print("=" * 50)
    
    # Test audio system
    audio_ok = test_audio_system()
    
    if audio_ok:
        print("\n" + "🎉 Audio system looks good!")
        
        # Ask if user wants to test recording
        try:
            response = input("\nWould you like to test a 3-second recording? (y/n): ").lower()
            if response == 'y':
                recording_ok = test_basic_recording()
                if recording_ok:
                    print("\n✅ All tests passed! Ready for next step.")
                else:
                    print("\n⚠️ Recording test failed. Check microphone connection.")
        except KeyboardInterrupt:
            print("\n\nTest cancelled by user.")
    else:
        print("\n❌ Audio system issues detected. Please fix before continuing.")
        sys.exit(1)
