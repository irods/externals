all : avro boost clang cmake cppzmq fmt jsoncons jwt-cpp mungefs nanodbc qpid-proton redis spdlog

server : boost clang fmt jsoncons nanodbc spdlog

.PHONY : all server clean $(all)

BUILD_OPTIONS=-v

packages.mk : Makefile versions.json build.py
	./build.py packagesfile

-include packages.mk

$(all) : packages.mk

$(AVRO_PACKAGE) : $(BOOST_PACKAGE) $(CMAKE_PACKAGE) $(CLANG_PACKAGE)
	./build.py $(BUILD_OPTIONS) avro > avro.log 2>&1
avro : $(AVRO_PACKAGE)
avro_clean :
	@echo "Cleaning avro..."
	@rm -rf avro*
	@rm -rf $(AVRO_PACKAGE)

$(BOOST_PACKAGE) : $(CLANG_PACKAGE)
	./build.py $(BUILD_OPTIONS) boost > boost.log 2>&1
boost : $(BOOST_PACKAGE)
boost_clean :
	@echo "Cleaning boost..."
	@rm -rf boost*
	@rm -rf $(BOOST_PACKAGE)

$(CLANG_PACKAGE) : $(CMAKE_PACKAGE)
	./build.py $(BUILD_OPTIONS) clang > clang.log 2>&1
clang : $(CLANG_PACKAGE)
clang_clean :
	@echo "Cleaning clang..."
	@rm -rf clang*
	@rm -rf $(CLANG_PACKAGE)

$(CMAKE_PACKAGE) :
	./build.py $(BUILD_OPTIONS) cmake > cmake.log 2>&1
cmake : $(CMAKE_PACKAGE)
cmake_clean :
	@echo "Cleaning cmake..."
	@rm -rf cmake*
	@rm -rf $(CMAKE_PACKAGE)

$(CPPZMQ_PACKAGE) :
	./build.py $(BUILD_OPTIONS) cppzmq > cppzmq.log 2>&1
cppzmq : $(CPPZMQ_PACKAGE)
cppzmq_clean :
	@echo "Cleaning cppzmq..."
	@rm -rf cppzmq*
	@rm -rf $(CPPZMQ_PACKAGE)

$(FMT_PACKAGE) : $(CLANG_PACKAGE)
	./build.py $(BUILD_OPTIONS) fmt > fmt.log 2>&1
fmt : $(FMT_PACKAGE)
fmt_clean :
	@echo "Cleaning fmt..."
	@rm -rf fmt*
	@rm -rf $(FMT_PACKAGE)

$(JSONCONS_PACKAGE) : $(CMAKE_PACKAGE)
	./build.py $(BUILD_OPTIONS) jsoncons > jsoncons.log 2>&1
jsoncons : $(JSONCONS_PACKAGE)
jsoncons_clean :
	@echo "Cleaning jsoncons..."
	@rm -rf jsoncons*
	@rm -rf $(JSONCONS_PACKAGE)

$(JWT-CPP_PACKAGE) : $(CMAKE_PACKAGE)
	./build.py $(BUILD_OPTIONS) jwt-cpp > jwt-cpp.log 2>&1
jwt-cpp : $(JWT-CPP_PACKAGE)
jwt-cpp_clean :
	@echo "Cleaning jwt-cpp..."
	@rm -rf jwt-cpp*
	@rm -rf $(JWT-CPP_PACKAGE)

$(MUNGEFS_PACKAGE) : $(CPPZMQ_PACKAGE) $(AVRO_PACKAGE)
	./build.py $(BUILD_OPTIONS) mungefs > mungefs.log 2>&1
mungefs : $(MUNGEFS_PACKAGE)
mungefs_clean :
	@echo "Cleaning mungefs..."
	@rm -rf mungefs*
	@rm -rf $(MUNGEFS_PACKAGE)

$(NANODBC_PACKAGE) : $(CLANG_PACKAGE)
	./build.py $(BUILD_OPTIONS) nanodbc > nanodbc.log 2>&1
nanodbc : $(NANODBC_PACKAGE)
nanodbc_clean :
	@echo "Cleaning nanodbc..."
	@rm -rf nanodbc*
	@rm -rf $(NANODBC_PACKAGE)

$(QPID-PROTON_PACKAGE) : $(CLANG_PACKAGE)
	./build.py $(BUILD_OPTIONS) qpid-proton > qpid-proton.log 2>&1
qpid-proton : $(QPID-PROTON_PACKAGE)
qpid-proton_clean :
	@echo "Cleaning qpid-proton..."
	@rm -rf qpid-proton*
	@rm -rf $(QPID-PROTON_PACKAGE)

$(REDIS_PACKAGE) : $(CLANG_PACKAGE)
	./build.py $(BUILD_OPTIONS) redis > redis.log 2>&1
redis : $(REDIS_PACKAGE)
redis_clean :
	@echo "Cleaning redis..."
	@rm -rf redis*
	@rm -rf $(REDIS_PACKAGE)

$(SPDLOG_PACKAGE) : $(FMT_PACKAGE)
	./build.py $(BUILD_OPTIONS) spdlog > spdlog.log 2>&1
spdlog : $(SPDLOG_PACKAGE)
spdlog_clean :
	@echo "Cleaning spdlog..."
	@rm -rf spdlog*
	@rm -rf $(SPDLOG_PACKAGE)

clean : avro_clean boost_clean clang_clean cmake_clean cppzmq_clean fmt_clean jsoncons_clean jwt-cpp_clean mungefs_clean nanodbc_clean qpid-proton_clean redis_clean spdlog_clean
	@echo "Cleaning generated files..."
	@rm -rf packages.mk
	@echo "Done."
