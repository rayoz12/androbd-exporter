# AndroOBD Exporter
Have you ever thought "What am I doing with my life if I'm not storing and visualising my engine RPM on a daily basis?" No? Just me? Well fear not this tool bridges the gap between the data in your car and your prometheus instance. It leverages AndrOBD to read and store the data in an MQTT broker and this just reads that data and returns it when scraped.

This tool reads andrOBD data being stored in an MQTT broker and gives it to prometheus when scraped as an exporter.

# AndrOBD-Exporter Configuration
All configuration is stored in the [.env.example](.env.example) which is also able to configured as environment variables. Refer to the [docker-compose.yml](docker-compose.yml) for an example.

If you don't have SSL setup properly on your broker you can configure `MQTT_IGNORE_INVALID_CERTS=TRUE` to ignore any protential SSL errors, however I discourage this as your traffic can be read by anyone.

# AndrOBD Configuration
1. You need AndrOBD configured and reading data from your OBDII device.
2. Make sure it's connected and displaying your car data.
3. Install the AndrOBD-MQTTPublisher plugin [Available on F-Droid](https://f-droid.org/en/packages/com.fr3ts0n.androbd.plugin.mqtt/)
    1. Information on how to configure it is available here: https://github.com/fr3ts0n/AndrOBD-Plugin/tree/master/MqttPublisher
4. Configure it to publish it to your broker
5. Take note of the message prefix you set (aka the topic)
6. Have a look at your message broker to make sure the data is available
    1. I recommend [MQTT Explorer](http://mqtt-explorer.com/)

# Prometheus Configuration
1. Add the following job to your `prometheus.yml` file, noting the ip address on the last line pointing to the exporter:
```yaml
  - job_name: 'androbd'
    metrics_path: "/"
    # Override the global default and scrape targets from this job every 5 seconds.
    scrape_interval: 30s
  
    static_configs:
      - targets: ["Ryan's Mitsubishi Lancer"]
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: 192.168.1.103:3000 # Server exporter
```

# Thanks
- None of this would be possible without the great, *open-source* and easily intergratable software that is [AndrOBD](https://github.com/fr3ts0n/AndrOBD). 
