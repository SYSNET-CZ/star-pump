# STAR PUMPA

Pumpuje data zu katalogu STaR do Elasticsearch. 
Pumpa běží každou hodinu ve dvanácz minut po celé. 


## Docker

Obraz se postaví příkazem:

    docker build -t sysnetcz/star-pump .
    
Při vytváření docker containeru je třeba mít na vědomí, že kontejner spolupracuje s elasticseach a CKAN.  
Oby tyto kontejnery musí být pro kontejner dostupný. Ideální je umístit kontejner do stejné sítě jako kontejnery 
elasticsearch a ckan.

    docker run -d p 5080:5000 --network docker_backend -t sysnetcz/star-pump      

Pro zachování bezstavovosti kontejneru je třeba umístit datocé adresáře vně kontejneru. Například:

    docker volume create pump_logs
    docker volume create pump_data
    docker volume create pump_syslog
    
    docker run -d \
        -v pump_logs:/opt/pump/logs \
        -v pump_data:/opt/pump/data  \
        -v pump_syslog:/var/log  \
        -t sysnetcz/star-pump

    docker run -d \
        --network docker_backend \
        --name pumpa \
        -p 5000:5000 \
        -v pump_logs:/opt/pump/logs \
        -v pump_data:/opt/pump/data  \
        -v pump_syslog:/var/log  \
        -t sysnetcz/star-pump
