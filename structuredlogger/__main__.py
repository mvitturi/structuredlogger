from structuredlogger.logger import config


def main():
    config.initialize()
    logger = config.get_logger(__name__)
    logger.info("Test Application {execution_id} started")
    logger.warning("The product {product_id} is too big", product_id=987163)
    print("Done!")


if __name__ == '__main__':
    main()
