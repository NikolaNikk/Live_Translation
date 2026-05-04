from asr.client import main as run_asr

if __name__ == "__main__":
    run_asr()


#python simulstreaming_whisper_server.py --language en --task transcribe --host 127.0.0.1 --port 43001 --out-txt --beams 1 --decoder greedy --min-chunk-size 0.4 --audio_min_len 0.4 --audio_max_len 4 --no-never_fire
