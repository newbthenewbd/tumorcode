cmake_minimum_required(VERSION 2.6)
#PROJECT(programs)

include_directories(../common)
include_directories(${ADDITIONAL_INCLUDE_DIRS})

#add_executable(tests tests.cpp)
#target_link_libraries(tests ${myLibs})

# add_executable(test_convection test_convection1.cpp)
# target_link_libraries(test_convection ${myLibs})

add_executable(test_stepper test_stepper.cpp)
target_link_libraries(test_stepper ${myLibs})

# add_executable(test_level_set test_level_set.cpp)
# target_link_libraries(test_level_set ${myLibs})

add_executable(test_elliptic_solver test_elliptic_solver.cpp)
target_link_libraries(test_elliptic_solver ${myLibs})

# add_executable(test_convection_diffusion test_convection_diffusion.cpp)
# target_link_libraries(test_convection_diffusion ${myLibs})

install(TARGETS test_stepper test_elliptic_solver RUNTIME DESTINATION bin)
