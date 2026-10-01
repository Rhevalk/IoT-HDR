RoadMap
> Linux
    ... Broker
> Network
> Fullstack Developer
    ... Frontend
    ... Backend
    ... Database
> Embedded

rsync -avz -e ssh --exclude-from='.exclude' ./ orangepi@192.168.1.128:/home/orangepi/projects/IoT
rsync -av --delete --exclude-from='.exclude' ./ arcshzen@192.168.1.12:/home/orangepi/projects/IoT/

