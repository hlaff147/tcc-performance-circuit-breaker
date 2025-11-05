import os

# Criar diretório para os diagramas se não existir
puml_dir = os.path.join("docs", "diagramas", "puml")
os.makedirs(puml_dir, exist_ok=True)

# Estilo comum para todos os diagramas
COMMON_STYLE = '''
skinparam backgroundColor white
skinparam handwritten false
skinparam defaultFontName Arial
skinparam defaultFontSize 12

skinparam package {
    backgroundColor<<Application>> #d4f3ef
    borderColor<<Application>> #2d938e
    backgroundColor #f8f9fa
    borderColor #dee2e6
    fontColor #212529
}

skinparam component {
    backgroundColor #f8f9fa
    borderColor #6c757d
    fontColor #212529
}

skinparam cloud {
    backgroundColor #f8f9fa
    borderColor #6c757d
    fontColor #212529
}

skinparam database {
    backgroundColor #f8f9fa
    borderColor #6c757d
    fontColor #212529
}

skinparam arrow {
    color #6c757d
    fontColor #495057
}

skinparam actor {
    backgroundColor #f8f9fa
    borderColor #6c757d
    fontColor #212529
}

skinparam note {
    backgroundColor #fff3cd
    borderColor #ffeeba
    fontColor #856404
}
'''

def create_diagram(name, content):
    """Helper function to create a diagram with common style"""
    return '@startuml ' + name + '\n' + COMMON_STYLE + '\n' + content + '\n@enduml'

# Diagrama 1: Arquitetura Geral do Experimento
ARCHITECTURE_DIAGRAM = create_diagram('arquitetura_geral', '''
allowmixing

actor "k6 (Load Tester)" as k6
actor "Aluno (Pesquisador)" as pesquisador

node "Docker Host" {
    component "servico-pagamento" as pagamento
    component "servico-adquirente" as adquirente
    
    package "Stack de Monitoramento" {
        component "Prometheus" as prometheus
        component "Grafana" as grafana
        component "cAdvisor" as cadvisor
    }
}

k6 --> pagamento : [HTTP POST /pagar]
pagamento --> adquirente : [HTTP POST /autorizar (Feign)]
cadvisor --> pagamento : [Monitora Container]
cadvisor --> adquirente : [Monitora Container]
prometheus --> pagamento : [Scrape: /actuator/prometheus]
prometheus --> cadvisor : [Scrape: Métricas de CPU/Memória]
grafana --> prometheus : [Query: PromQL]
pesquisador --> grafana : [Visualiza Dashboards]
''')

# Diagrama 2: Componentes Internos do servico-pagamento
COMPONENTS_DIAGRAM = create_diagram('componentes_internos', '''
allowmixing

package "Controllers" {
    class PagamentoController {
        +pagar(PagamentoRequest)
    }
}

package "Services" {
    class PagamentoService {
        +processarPagamento(...)
    }
}

package "Clients (Feign)" {
    interface AdquirenteClient {
        +autorizar(AutorizacaoRequest)
    }
}

package "Resilience (CB)" {
    artifact "Resilience4j (CircuitBreaker)" as CB
    class PagamentoFallback {
        +handleFalhaAdquirente(Throwable t)
    }
}

PagamentoController --> PagamentoService
PagamentoService --> CB
CB --> AdquirenteClient : (no estado FECHADO)
CB ..> PagamentoFallback : (no estado ABERTO ou em erro)
AdquirenteClient -[hidden]- PagamentoFallback
''')

# Diagrama 3: Sequência de Falha - V1
SEQUENCE_V1_DIAGRAM = create_diagram('sequencia_falha_v1', '''
actor k6
participant "servico-pagamento (V1)" as Pagamento
participant "servico-adquirente" as Adquirente

k6 -> Pagamento: POST /pagar
activate Pagamento

Pagamento -> Adquirente: POST /autorizar
activate Adquirente
Adquirente --> Pagamento: HTTP 503 (Service Unavailable)
deactivate Adquirente

note right of Pagamento: Thread bloqueada!\\nConsome recursos esperando timeout.

Pagamento --> k6: HTTP 500 (Internal Server Error)
deactivate Pagamento

note over k6, Adquirente: "Falha em cascata: k6 recebe erro, Pagamento sofreu sobrecarga."
''')

# Diagrama 4: Sequência de Resiliência - V2
SEQUENCE_V2_DIAGRAM = create_diagram('sequencia_resiliencia_v2', '''
actor k6
participant "servico-pagamento (V2)\\n[CB: FECHADO]" as Pagamento
participant "FallbackHandler" as Fallback
participant "servico-adquirente" as Adquirente

group Primeiras Chamadas (Circuito FECHADO)
    k6 -> Pagamento: POST /pagar
    activate Pagamento
    Pagamento -> Adquirente: POST /autorizar
    Adquirente --> Pagamento: HTTP 503 (Falha)
    Pagamento --> k6: HTTP 500 (Erro inicial)
    deactivate Pagamento
    note right of Pagamento: Contador de falha incrementado.
end

... Algum tempo depois ...

note over Pagamento: Taxa de falha atingida!\\n**Circuito ABERTO**

group Próximas Chamadas (Circuito ABERTO)
    k6 -> Pagamento: POST /pagar
    activate Pagamento
    note right of Pagamento: Fail-Fast! Chamada bloqueada pelo CB.
    Pagamento ->> Fallback: executarFallback(exception)
    activate Fallback
    Fallback -->> Pagamento: (Dados de contingência)
    deactivate Fallback
    Pagamento --> k6: HTTP 202 Accepted
    deactivate Pagamento
end

note over Fallback, Adquirente: "Sistema protegido: 'servico-adquirente' não é acionado, 'k6' recebe sucesso."
''')

# Diagrama 5: Stack de Monitoramento
MONITORING_DIAGRAM = create_diagram('stack_monitoramento', '''
allowmixing

cloud "Prometheus" {
    database "TSDB"
}

component "cAdvisor" as cadvisor
component "servico-pagamento" as pagamento
component "Grafana" as grafana
artifact "k6 (JSON Output)" as k6_output
component "k6" as k6
artifact "Python (Script de Análise)" as python

Prometheus <-- cadvisor : [scrape: container_cpu,\\ncontainer_memory]
Prometheus <-- pagamento : [scrape: /actuator/prometheus]\\n(jvm_threads, tomcat_threads,\\nresilience4j_state, ...)

k6 -> k6_output : [Gera: p95, req_rate, errors]

grafana -> Prometheus : [Query: PromQL]
python -> Prometheus : [API Query (Automação)]
python -> k6_output : [Lê JSON]
''')

# Lista de diagramas para gerar
diagrams = {
    "arquitetura_geral.puml": ARCHITECTURE_DIAGRAM,
    "componentes_internos.puml": COMPONENTS_DIAGRAM,
    "sequencia_falha_v1.puml": SEQUENCE_V1_DIAGRAM,
    "sequencia_resiliencia_v2.puml": SEQUENCE_V2_DIAGRAM,
    "stack_monitoramento.puml": MONITORING_DIAGRAM
}

# Gerar todos os diagramas
for filename, content in diagrams.items():
    filepath = os.path.join(puml_dir, filename)
    with open(filepath, "w") as f:
        f.write(content)
    print(f"Gerado: {filepath}")

print("\nTodos os diagramas foram gerados com sucesso!")
print("Para gerar as imagens, instale o PlantUML e execute:")
print(f"java -jar plantuml.jar {puml_dir}/*.puml")