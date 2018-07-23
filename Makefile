all : autoconf avro aws-sdk-cpp boost clang clang-runtime cmake cpython imagemagick jansson json libarchive libs3 qpid qpid-proton qpid-with-proton redis zeromq4-1 cppzmq

.PHONY : all clean $(all)

VERBOSITY=-v

packages.mk : Makefile versions.json build.py
	./build.py packagesfile

-include packages.mk

$(all) : packages.mk

$(AUTOCONF_PACKAGE) :
	./build.py $(VERBOSITY) autoconf > autoconf.log 2>&1
autoconf : $(AUTOCONF_PACKAGE)
autoconf_clean :
	@echo "Cleaning autoconf..."
	@rm -rf autoconf*
	@rm -rf $(AUTOCONF_PACKAGE)

$(AVRO_PACKAGE) : $(BOOST_PACKAGE) $(CMAKE_PACKAGE) $(CLANG_PACKAGE)
	./build.py $(VERBOSITY) avro > avro.log 2>&1
avro : $(AVRO_PACKAGE)
avro_clean :
	@echo "Cleaning avro..."
	@rm -rf avro*
	@rm -rf $(AVRO_PACKAGE)

$(AWS-SDK-CPP_PACKAGE) : $(CMAKE_PACKAGE) $(CLANG_PACKAGE)
	./build.py $(VERBOSITY) aws-sdk-cpp > aws-sdk-cpp.log 2>&1
aws-sdk-cpp : $(AWS-SDK-CPP_PACKAGE)
aws-sdk-cpp_clean :
	@echo "Cleaning aws-sdk-cpp..."
	@rm -rf aws-sdk-cpp*
	@rm -rf $(AWS-SDK-CPP_PACKAGE)

$(BOOST_PACKAGE) : $(CLANG_PACKAGE)
	./build.py $(VERBOSITY) boost > boost.log 2>&1
boost : $(BOOST_PACKAGE)
boost_clean :
	@echo "Cleaning boost..."
	@rm -rf boost*
	@rm -rf $(BOOST_PACKAGE)

$(CLANG_PACKAGE) : $(CMAKE_PACKAGE) $(CPYTHON_PACKAGE)
	./build.py $(VERBOSITY) clang > clang.log 2>&1
clang : $(CLANG_PACKAGE)
clang_clean :
	@echo "Cleaning clang..."
	@rm -rf clang*
	@rm -rf $(CLANG_PACKAGE)

$(CLANG-RUNTIME_PACKAGE) : $(CLANG_PACKAGE)
	./build.py $(VERBOSITY) clang-runtime > clang-runtime.log 2>&1
clang-runtime : $(CLANG-RUNTIME_PACKAGE)
clang-runtime_clean :
	@echo "Cleaning clang-runtime..."
	@rm -rf clang-runtime*
	@rm -rf $(CLANG-RUNTIME_PACKAGE)

$(CMAKE_PACKAGE) :
	./build.py $(VERBOSITY) cmake > cmake.log 2>&1
cmake : $(CMAKE_PACKAGE)
cmake_clean :
	@echo "Cleaning cmake..."
	@rm -rf cmake*
	@rm -rf $(CMAKE_PACKAGE)

$(CPYTHON_PACKAGE) :
	./build.py $(VERBOSITY) cpython > cpython.log 2>&1
cpython : $(CPYTHON_PACKAGE)
cpython_clean :
	@echo "Cleaning cpython..."
	@rm -rf cpython*
	@rm -rf $(CPYTHON_PACKAGE)

$(IMAGEMAGICK_PACKAGE) : $(CLANG_PACKAGE)
	./build.py $(VERBOSITY) imagemagick > imagemagick.log 2>&1
imagemagick : $(IMAGEMAGICK_PACKAGE)
imagemagick_clean :
	@echo "Cleaning imagemagick..."
	@rm -rf imagemagick*
	@rm -rf $(IMAGEMAGICK_PACKAGE)

$(JANSSON_PACKAGE) : $(CLANG_PACKAGE)
	./build.py $(VERBOSITY) jansson > jansson.log 2>&1
jansson : $(JANSSON_PACKAGE)
jansson_clean :
	@echo "Cleaning jansson..."
	@rm -rf jansson*
	@rm -rf $(JANSSON_PACKAGE)

$(JSON_PACKAGE) :
	./build.py $(VERBOSITY) json > json.log 2>&1
json : $(JSON_PACKAGE)
json_clean :
	@echo "Cleaning json..."
	@rm -rf json*
	@rm -rf $(JSON_PACKAGE)

$(LIBARCHIVE_PACKAGE) : $(CMAKE_PACKAGE) $(CLANG_PACKAGE)
	./build.py $(VERBOSITY) libarchive > libarchive.log 2>&1
libarchive : $(LIBARCHIVE_PACKAGE)
libarchive_clean :
	@echo "Cleaning libarchive..."
	@rm -rf libarchive*
	@rm -rf $(LIBARCHIVE_PACKAGE)

$(LIBS3_PACKAGE) : $(CLANG_PACKAGE)
	./build.py $(VERBOSITY) libs3 > libs3.log 2>&1
libs3 : $(LIBS3_PACKAGE)
libs3_clean :
	@echo "Cleaning libs3..."
	@rm -rf libs3*
	@rm -rf $(LIBS3_PACKAGE)

$(QPID_PACKAGE) : $(CLANG_PACKAGE) $(BOOST_PACKAGE) $(QPID-PROTON_PACKAGE)
	./build.py $(VERBOSITY) qpid > qpid.log 2>&1
qpid : $(QPID_PACKAGE)
qpid_clean :
	@echo "Cleaning qpid..."
	@rm -rf qpid*
	@rm -rf $(QPID_PACKAGE)

$(QPID-PROTON_PACKAGE) : $(CLANG_PACKAGE)
	./build.py $(VERBOSITY) qpid-proton > qpid-proton.log 2>&1
qpid-proton : $(QPID-PROTON_PACKAGE)
qpid-proton_clean :
	@echo "Cleaning qpid-proton..."
	@rm -rf qpid-proton*
	@rm -rf $(QPID-PROTON_PACKAGE)

$(QPID-WITH-PROTON_PACKAGE) : $(QPID_PACKAGE)
	./build.py $(VERBOSITY) qpid-with-proton > qpid-with-proton.log 2>&1
qpid-with-proton : $(QPID-WITH-PROTON_PACKAGE)
qpid-with-proton_clean :
	@echo "Cleaning qpid-with-proton..."
	@rm -rf qpid-with-proton*
	@rm -rf $(QPID-WITH-PROTON_PACKAGE)

$(REDIS_PACKAGE) : $(CLANG_PACKAGE)
	./build.py $(VERBOSITY) redis > redis.log 2>&1
redis : $(REDIS_PACKAGE)
redis_clean :
	@echo "Cleaning redis..."
	@rm -rf redis*
	@rm -rf $(REDIS_PACKAGE)

$(ZEROMQ4-1_PACKAGE) : $(CLANG_PACKAGE)
	./build.py $(VERBOSITY) zeromq4-1 > zeromq4-1.log 2>&1
zeromq4-1 : $(ZEROMQ4-1_PACKAGE)
zeromq4-1_clean :
	@echo "Cleaning zeromq4-1..."
	@rm -rf zeromq4-1*
	@rm -rf $(ZEROMQ4-1_PACKAGE)

$(CPPZMQ_PACKAGE) :
	./build.py $(VERBOSITY) cppzmq > cppzmq.log 2>&1
cppzmq : $(CPPZMQ_PACKAGE)
cppzmq_clean :
	@echo "Cleaning cppzmq..."
	@rm -rf cppzmq*
	@rm -rf $(CPPZMQ_PACKAGE)

clean : autoconf_clean avro_clean aws-sdk-cpp_clean boost_clean clang_clean clang-runtime_clean cmake_clean cpython_clean jansson_clean libarchive_clean libs3_clean zeromq4-1_clean cppzmq_clean
	@echo "Cleaning generated files..."
	@rm -rf packages.mk
	@echo "Done."
