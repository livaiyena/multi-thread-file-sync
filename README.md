# Multi-Thread File Sync

## Amaç
Kaynak klasörü hedef klasöre senkronize eden, eksik ve değişen dosyaları çoklu thread ile kopyalayan bir POSIX/C aracı.

## Tasarım

Program **Producer-Consumer** modeli kullanır:
- **Producer** (scanner): Kaynak dizini recursive tarar, kopyalanacak dosyaları thread-safe kuyruğa ekler.
- **Consumer** (worker threads): Kuyruktan görev alıp dosyaları 64KB bloklar halinde kopyalar.

```
  scanner (producer) → task_queue (mutex+cond) → worker threads (consumers)
                                                       ↓
                                                 logger (mutex)
```

| Modül | Dosya | Sorumluluk |
|-------|-------|------------|
| Scanner | `scanner.c`, `scanner_utils.c` | Recursive dizin tarama, dosya karşılaştırma |
| Task Queue | `task_queue.c` | Thread-safe FIFO kuyruk |
| Thread Pool | `thread_pool.c` | Worker thread yönetimi |
| File Copy | `file_copy.c`, `file_copy_utils.c` | Blok blok kopyalama, dizin oluşturma |
| Logger | `logger.c` | Thread-safe loglama |
| Performance | `perf.c` | Zaman ölçümü ve rapor |
| Error | `error.c` | Hata yönetimi |

## Kullanılan Sistem Programlama Kavramları

- **POSIX Threads**: `pthread_create`, `pthread_join` ile thread pool
- **Mutex**: Task queue, log dosyası ve performans sayaçları için 3 ayrı mutex
- **Condition Variable**: `pthread_cond_wait`/`pthread_cond_broadcast` ile görev bekleme ve shutdown
- **File I/O**: `open`, `read`, `write`, `close` ile 64KB blok kopyalama
- **Directory I/O**: `opendir`, `readdir`, `stat`, `mkdir`, `chmod`
- **Zaman ölçümü**: `clock_gettime(CLOCK_MONOTONIC)`

## Çalıştırma Adımları

```bash
make                                    # Derleme
./filesync <kaynak> <hedef> [thread]    # Çalıştırma (varsayılan: 4 thread)
make test                               # Hızlı doğrulama testi
make pytest                             # Python test suite (17 test)
make benchmark                          # Performans karşılaştırması
```

## Testler

### Hızlı Test (`make test`)
Test dizinleri oluşturur, 4 thread ile senkronize eder, `diff` ile doğrular.

### Python Test Suite (`make pytest`)
17 test, 39 assertion — 3 modülde organize:

| Dosya | Testler |
|-------|---------|
| `test_basic.py` | Basit sync, recursive dizin, boş dizin, hatalı argüman |
| `test_files.py` | Büyük dosya (5MB), değişen dosya, izinler, 100 dosya |
| `test_threads.py` | 1/2/4/8 thread doğruluk, loglama, performans benchmark |

### Performans Testi ve Karşılaştırması (`make benchmark`)
`benchmark.sh` betiği ile 1, 2, 4, 8 thread kullanılarak kopyalama hızları (MB/s) karşılaştırılır.

#### Örnek Performans Değerlendirmesi
100 adet dosyadan (toplam 10MB) oluşan bir veri seti üzerinde yapılan test sonuçları aşağıdadır:

| Thread Sayısı | Geçen Süre (sn) | Veri Hızı (Throughput) | Hızlanma (Speedup) |
|---------------|-----------------|------------------------|--------------------|
| 1 Thread      | 0.1824 s        | 54.82 MB/s             | 1.00x (Referans)   |
| 2 Thread      | 0.0984 s        | 101.62 MB/s            | 1.85x              |
| 4 Thread      | 0.0542 s        | 184.50 MB/s            | 3.37x              |
| 8 Thread      | 0.0381 s        | 262.46 MB/s            | 4.79x              |

- **Değerlendirme (Hız Değişimi):** Thread sayısı artırıldığında I/O işlemleri paralel olarak yürütüldüğü için toplam çalışma süresi kısalmış ve throughput artmıştır. 1 thread'den 4 thread'e geçildiğinde **~3.37 kat** hız artışı elde edilmiştir. 8 thread'e çıkıldığında ise disk yazma hızı limiti (I/O Bottleneck) ve context switch maliyetleri nedeniyle hızlanma oranı doğrusal artışını yavaşlatmıştır.
- **I/O Performansı / Gecikme:** Okuma ve yazma işlemlerinde 64KB `BLOCK_SIZE` kullanılması, sistem çağrısı (read/write syscall) sayısını azaltarak I/O gecikmelerini minimize etmektedir.


## Karşılaşılan Problemler

1. **Race Condition**: Log dosyasına mutex olmadan yazılınca satırlar karışıyordu → `pthread_mutex_lock` eklendi.
2. **Thread Shutdown**: Worker'lar boş kuyrukta sonsuza kadar bekliyordu → `shutdown` flag + `pthread_cond_broadcast`.
3. **Dizin Sırası**: Hedef dizin yokken dosya kopyalamaya çalışılıyordu → `mkdir_recursive()` eklendi.
4. **I/O Performansı**: 4KB buffer yavaştı → 64KB `BLOCK_SIZE` ile throughput arttı.
5. **Path Overflow**: Uzun yollar için `MAX_PATH_LEN` + `snprintf` güvenliği eklendi.
6. **mtime Çözünürlüğü**: Saniye bazlı mtime yetmiyordu → boyut + mtime birlikte kontrol ediliyor.
7. **Stat Check**: Kaynak dizin için `S_ISDIR` kontrolü eklendi, ondan önce çalışıyormuş gibi gözüküyordu ve Success olarak gözüküyordu.
