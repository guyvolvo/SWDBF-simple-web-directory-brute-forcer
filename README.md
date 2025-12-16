# **Steps:** 

### **Input**
- Base URL
- Wordlist
- Extensions (optional)
- Threads
- Timeout / rate limits

### **Engine**
- URL generator
- Worker pool (threads)
- HTTP client
- Response evaluator

### **Output**
- Found paths
- Status codes
- Errors / retries

## Features Explained
_Multi-Threading_
Uses Python's ThreadPoolExecutor to send multiple concurrent requests, dramatically improving scan speed.
_False Positive Detection_
Automatically filters responses that return 200 status codes but contain error messages like "not found", "invalid request", or "error".
_Thread-Safe Output_
Uses locks to ensure clean, non-overlapping console output even with multiple threads running.
Graceful Shutdown

_Performance Tips_
5-10 threads: Safe, respectful scanning
10-20 threads: Fast scanning for most targets
20-50 threads: Aggressive (may trigger rate limiting)

⚠️ Warning: Using too many threads may overload target servers or trigger security measures. Always scan responsibly and only on systems you have permission to test.
